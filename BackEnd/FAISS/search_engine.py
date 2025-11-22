#!/usr/bin/env python3
"""
FAISS-Based Semantic Search Engine for D&D SRD Content
Enables fast lookup of spells, monsters, items, rules, etc.
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import re


# Check for FAISS availability
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not installed. Install with: pip install faiss-cpu")


# Check for sentence transformers (for embeddings)
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️  sentence-transformers not installed. Install with: pip install sentence-transformers")


@dataclass
class SearchResult:
    """A single search result"""
    title: str
    content: str
    file_path: str
    category: str
    score: float
    snippet: str
    metadata: Dict = None
    
    def to_dict(self):
        return {
            'title': self.title,
            'content': self.content,
            'file_path': self.file_path,
            'category': self.category,
            'score': float(self.score),
            'snippet': self.snippet,
            'metadata': self.metadata or {}
        }


class SRDSearchEngine:
    """
    FAISS-powered semantic search for D&D SRD content
    
    Uses sentence embeddings for semantic similarity search,
    which understands meaning rather than just keywords.
    """
    
    def __init__(
        self,
        srd_path: str = "../../srd_story_cycle",
        index_path: str = "../search_index",
        model_name: str = "all-MiniLM-L6-v2"  # Fast, good quality
    ):
        self.srd_path = Path(srd_path)
        self.index_path = Path(index_path)
        self.index_path.mkdir(exist_ok=True)
        
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.metadata = []
        
        # Category mapping for better organization
        self.category_map = {
            'spells': ['spell', 'magic', 'cantrip', 'ritual'],
            'monsters': ['monster', 'creature', 'beast', 'npc'],
            'items': ['item', 'weapon', 'armor', 'gear', 'equipment'],
            'rules': ['rule', 'mechanic', 'combat', 'check'],
            'conditions': ['condition', 'status', 'effect'],
            'classes': ['class', 'subclass', 'archetype'],
            'races': ['race', 'ancestry', 'lineage']
        }
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        if not FAISS_AVAILABLE:
            print("❌ FAISS not available")
            return False
        if not EMBEDDINGS_AVAILABLE:
            print("❌ sentence-transformers not available")
            return False
        return True
    
    def load_model(self):
        """Load the sentence transformer model"""
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError("sentence-transformers not installed")
        
        print(f"📦 Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print("✓ Model loaded")
    
    def extract_documents_from_srd(self) -> List[Dict]:
        """
        Extract all searchable documents from SRD
        
        Returns list of dicts with:
        - title: Document title
        - content: Full text content
        - file_path: Source file
        - category: Content category
        """
        documents = []
        
        print(f"📚 Scanning SRD at {self.srd_path}")
        
        # Walk through all markdown files
        for md_file in self.srd_path.rglob("*.md"):
            if md_file.name in ['README.md', 'INDEX.md']:
                continue
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract title (first # header or filename)
                title = self._extract_title(content, md_file.name)
                
                # Determine category from file path
                category = self._determine_category(md_file)
                
                # Split into chunks if content is very long
                chunks = self._split_content(content, max_length=1000)
                
                for i, chunk in enumerate(chunks):
                    doc = {
                        'title': f"{title}" + (f" (Part {i+1})" if len(chunks) > 1 else ""),
                        'content': chunk,
                        'file_path': str(md_file.relative_to(self.srd_path)),
                        'category': category,
                        'chunk_id': i
                    }
                    documents.append(doc)
                    
            except Exception as e:
                print(f"⚠️  Error reading {md_file}: {e}")
        
        print(f"✓ Extracted {len(documents)} documents")
        return documents
    
    def _extract_title(self, content: str, filename: str) -> str:
        """Extract title from markdown content"""
        # Look for first # header
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Fall back to filename
        return filename.replace('.md', '').replace('_', ' ').title()
    
    def _determine_category(self, file_path: Path) -> str:
        """Determine content category from file path"""
        path_str = str(file_path).lower()
        
        for category, keywords in self.category_map.items():
            if any(keyword in path_str for keyword in keywords):
                return category
        
        return 'general'
    
    def _split_content(self, content: str, max_length: int = 1000) -> List[str]:
        """
        Split long content into chunks
        Tries to split on section headers or paragraphs
        """
        if len(content) <= max_length:
            return [content]
        
        chunks = []
        
        # Split on ## headers first
        sections = re.split(r'\n##\s+', content)
        
        for section in sections:
            if len(section) <= max_length:
                chunks.append(section)
            else:
                # Split long sections into paragraphs
                paragraphs = section.split('\n\n')
                current_chunk = ""
                
                for para in paragraphs:
                    if len(current_chunk) + len(para) <= max_length:
                        current_chunk += para + "\n\n"
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = para + "\n\n"
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content[:max_length]]
    
    def build_index(self, force_rebuild: bool = False):
        """
        Build FAISS index from SRD content
        
        Args:
            force_rebuild: If True, rebuild even if index exists
        """
        if not self._check_dependencies():
            raise RuntimeError("Missing required dependencies")
        
        index_file = self.index_path / "faiss.index"
        docs_file = self.index_path / "documents.pkl"
        
        # Check if index already exists
        if not force_rebuild and index_file.exists() and docs_file.exists():
            print("📂 Loading existing index...")
            self.load_index()
            return
        
        print("🔨 Building new search index...")
        
        # Load model
        if self.model is None:
            self.load_model()
        
        # Extract documents
        self.documents = self.extract_documents_from_srd()
        
        if not self.documents:
            raise ValueError("No documents found in SRD")
        
        # Generate embeddings
        print("🧮 Generating embeddings...")
        texts = [doc['title'] + "\n\n" + doc['content'] for doc in self.documents]
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Create FAISS index
        print("🔧 Creating FAISS index...")
        dimension = embeddings.shape[1]
        
        # Use IndexFlatIP for cosine similarity (Inner Product)
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype('float32'))
        
        # Save index and documents
        print("💾 Saving index...")
        faiss.write_index(self.index, str(index_file))
        
        with open(docs_file, 'wb') as f:
            pickle.dump(self.documents, f)
        
        print(f"✅ Index built successfully!")
        print(f"   - {len(self.documents)} documents indexed")
        print(f"   - Dimension: {dimension}")
    
    def load_index(self):
        """Load existing FAISS index"""
        if not self._check_dependencies():
            raise RuntimeError("Missing required dependencies")
        
        index_file = self.index_path / "faiss.index"
        docs_file = self.index_path / "documents.pkl"
        
        if not index_file.exists() or not docs_file.exists():
            raise FileNotFoundError("Index not found. Run build_index() first.")
        
        # Load model
        if self.model is None:
            self.load_model()
        
        # Load index
        self.index = faiss.read_index(str(index_file))
        
        # Load documents
        with open(docs_file, 'rb') as f:
            self.documents = pickle.load(f)
        
        print(f"✓ Index loaded ({len(self.documents)} documents)")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
        min_score: float = 0.3
    ) -> List[SearchResult]:
        """
        Search for relevant content
        
        Args:
            query: Search query
            top_k: Number of results to return
            category_filter: Optional category to filter by
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of SearchResult objects
        """
        if self.index is None or self.model is None:
            raise RuntimeError("Index not loaded. Call load_index() or build_index() first.")
        
        # Encode query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        # Get more results than needed for filtering
        search_k = top_k * 3 if category_filter else top_k
        scores, indices = self.index.search(query_embedding.astype('float32'), search_k)
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Invalid index
                continue
            
            doc = self.documents[idx]
            
            # Apply category filter
            if category_filter and doc['category'] != category_filter:
                continue
            
            # Apply score threshold
            if score < min_score:
                continue
            
            # Create snippet (first 200 chars)
            snippet = doc['content'][:200].strip()
            if len(doc['content']) > 200:
                snippet += "..."
            
            result = SearchResult(
                title=doc['title'],
                content=doc['content'],
                file_path=doc['file_path'],
                category=doc['category'],
                score=score,
                snippet=snippet,
                metadata={
                    'chunk_id': doc.get('chunk_id', 0)
                }
            )
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results
    
    def search_by_category(self, category: str, query: str = "", top_k: int = 10) -> List[SearchResult]:
        """Get all documents in a category, optionally filtered by query"""
        if query:
            return self.search(query, top_k=top_k, category_filter=category)
        
        # Return all documents in category
        results = []
        for doc in self.documents:
            if doc['category'] == category:
                snippet = doc['content'][:200].strip()
                if len(doc['content']) > 200:
                    snippet += "..."
                
                result = SearchResult(
                    title=doc['title'],
                    content=doc['content'],
                    file_path=doc['file_path'],
                    category=doc['category'],
                    score=1.0,
                    snippet=snippet
                )
                results.append(result)
        
        return results[:top_k]
    
    def get_categories(self) -> Dict[str, int]:
        """Get count of documents per category"""
        if not self.documents:
            return {}
        
        categories = {}
        for doc in self.documents:
            cat = doc['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        if not self.documents:
            return {'status': 'not_loaded'}
        
        return {
            'status': 'loaded',
            'total_documents': len(self.documents),
            'categories': self.get_categories(),
            'model': self.model_name,
            'index_dimension': self.index.d if self.index else 0
        }


# Flask API endpoints
def create_search_api(app, engine: SRDSearchEngine):
    """Add search endpoints to Flask app"""
    
    @app.route('/api/search', methods=['POST'])
    def api_search():
        from flask import request, jsonify
        
        data = request.json
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        category = data.get('category')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        try:
            results = engine.search(query, top_k=top_k, category_filter=category)
            return jsonify({
                'results': [r.to_dict() for r in results],
                'count': len(results)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/search/categories', methods=['GET'])
    def api_categories():
        from flask import jsonify
        try:
            categories = engine.get_categories()
            return jsonify({'categories': categories})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/search/stats', methods=['GET'])
    def api_stats():
        from flask import jsonify
        try:
            stats = engine.get_stats()
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# CLI for testing and building
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="D&D SRD Search Engine")
    parser.add_argument('--srd-path', default='../../srd_story_cycle', help='Path to SRD')
    parser.add_argument('--build', action='store_true', help='Build search index')
    parser.add_argument('--rebuild', action='store_true', help='Force rebuild index')
    parser.add_argument('--search', type=str, help='Search query')
    parser.add_argument('--category', type=str, help='Filter by category')
    parser.add_argument('--stats', action='store_true', help='Show index stats')
    
    args = parser.parse_args()
    
    engine = SRDSearchEngine(srd_path=args.srd_path)
    
    if args.build or args.rebuild:
        engine.build_index(force_rebuild=args.rebuild)
    
    elif args.stats:
        try:
            engine.load_index()
            stats = engine.get_stats()
            print("\n📊 Search Index Statistics")
            print("=" * 60)
            print(f"Status: {stats['status']}")
            print(f"Total Documents: {stats['total_documents']}")
            print(f"Model: {stats['model']}")
            print(f"Index Dimension: {stats['index_dimension']}")
            print("\nDocuments by Category:")
            for cat, count in stats['categories'].items():
                print(f"  {cat}: {count}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif args.search:
        try:
            engine.load_index()
            results = engine.search(args.search, category_filter=args.category)
            
            print(f"\n🔍 Search Results for: '{args.search}'")
            print("=" * 60)
            
            if not results:
                print("No results found.")
            else:
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result.title}")
                    print(f"   Category: {result.category}")
                    print(f"   Score: {result.score:.3f}")
                    print(f"   File: {result.file_path}")
                    print(f"   Snippet: {result.snippet}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()