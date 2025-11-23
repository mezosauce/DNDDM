#!/usr/bin/env python3

"""
•	Questioning State:
o	    Input: 
	        Story Predicament 
o	    Output: 
	        Accepted/ Declined
o	    Explanation: The goal here is to make sure when the LLM provides a situation where the player can only answer in a Accept/ Decline fashion, they are only limited to those two answers

"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable
from datetime import datetime
from enum import Enum
import re


class QuestionType(Enum):
    """Types of binary questions"""
    ACCEPT_DECLINE = "accept_decline"
    YES_NO = "yes_no"
    AGREE_REFUSE = "agree_refuse"
    TAKE_LEAVE = "take_leave"


class PlayerResponse(Enum):
    """Possible player responses"""
    ACCEPT = "accept"
    DECLINE = "decline"
    YES = "yes"
    NO = "no"
    AGREE = "agree"
    REFUSE = "refuse"
    TAKE = "take"
    LEAVE = "leave"
    INVALID = "invalid"


@dataclass
class QuestionContext:
    """Context for a binary question scenario"""
    question_id: str
    question_text: str
    question_type: QuestionType
    dm_prompt: str  # The full DM narration
    consequences_accept: Optional[str] = None
    consequences_decline: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)


@dataclass
class QuestionResponse:
    """Player's response to a question"""
    question_id: str
    response: PlayerResponse
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    player_input: str = ""  # Raw player input
    processed: bool = False


class QuestioningState:
    """
    Manages binary choice scenarios in the game.
    
    Use Cases:
    - NPC offers a deal: "Will you accept this quest?"
    - Moral dilemma: "Do you save the villagers or pursue the thief?"
    - Item interaction: "Do you take the cursed sword?"
    - Story branching: "Do you enter the dark cave or camp for the night?"
    """
    
    # Patterns that indicate a binary question
    QUESTION_PATTERNS = {
        QuestionType.ACCEPT_DECLINE: [
            r"(?:will you|do you)\s+accept",
            r"(?:will you|do you)\s+decline",
            r"accept\s+(?:the|this|my|his|her)",
            r"decline\s+(?:the|this|my|his|her)",
            r"what\s+(?:do you|will you)\s+(?:say|do|choose)\??",
            r"(?:accept|decline)\s+(?:or|/)",
        ],
        QuestionType.YES_NO: [
            r"(?:will you|do you)\s+\w+\??",
            r"(?:yes|no)\s+(?:or|/)",
            r"answer\s+(?:yes|no)",
        ],
        QuestionType.AGREE_REFUSE: [
            r"(?:will you|do you)\s+agree",
            r"(?:will you|do you)\s+refuse",
            r"(?:agree|refuse)\s+(?:or|/)",
        ],
        QuestionType.TAKE_LEAVE: [
            r"(?:will you|do you)\s+take",
            r"(?:will you|do you)\s+leave",
            r"(?:take|leave)\s+(?:it|the|this)",
            r"(?:take|leave)\s+(?:or|/)",
        ]
    }
    
    # Response mapping for normalization
    RESPONSE_MAPPING = {
        # Accept variants
        'accept': PlayerResponse.ACCEPT,
        'yes': PlayerResponse.ACCEPT,
        'agree': PlayerResponse.ACCEPT,
        'take': PlayerResponse.ACCEPT,
        'ok': PlayerResponse.ACCEPT,
        'okay': PlayerResponse.ACCEPT,
        'sure': PlayerResponse.ACCEPT,
        'fine': PlayerResponse.ACCEPT,
        'do it': PlayerResponse.ACCEPT,
        "i'll do it": PlayerResponse.ACCEPT,
        "i accept": PlayerResponse.ACCEPT,
        "i agree": PlayerResponse.ACCEPT,
        
        # Decline variants
        'decline': PlayerResponse.DECLINE,
        'no': PlayerResponse.DECLINE,
        'refuse': PlayerResponse.DECLINE,
        'leave': PlayerResponse.DECLINE,
        'nope': PlayerResponse.DECLINE,
        'pass': PlayerResponse.DECLINE,
        "i decline": PlayerResponse.DECLINE,
        "i refuse": PlayerResponse.DECLINE,
        "no thanks": PlayerResponse.DECLINE,
        "not interested": PlayerResponse.DECLINE,
    }
    
    def __init__(self):
        self.active_question: Optional[QuestionContext] = None
        self.question_history: List[QuestionContext] = []
        self.response_history: List[QuestionResponse] = []
        self.is_active: bool = False
        self._question_counter: int = 0
    
    def detect_question(self, dm_response: str) -> Optional[QuestionType]:
        """
        Detect if the DM's response contains a binary question.
        
        Args:
            dm_response: The DM's narration/response
            
        Returns:
            QuestionType if detected, None otherwise
        """
        dm_lower = dm_response.lower()
        
        # Check each question type's patterns
        for q_type, patterns in self.QUESTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, dm_lower):
                    return q_type
        
        return None
    
    def activate_question(
        self,
        dm_response: str,
        question_type: Optional[QuestionType] = None,
        consequences_accept: Optional[str] = None,
        consequences_decline: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> QuestionContext:
        """
        Activate a questioning state based on DM response.
        
        Args:
            dm_response: Full DM narration
            question_type: Type of question (auto-detected if None)
            consequences_accept: What happens if player accepts
            consequences_decline: What happens if player declines
            metadata: Additional context
            
        Returns:
            QuestionContext object
        """
        if question_type is None:
            question_type = self.detect_question(dm_response)
            if question_type is None:
                question_type = QuestionType.ACCEPT_DECLINE  # Default
        
        self._question_counter += 1
        question_id = f"Q{self._question_counter:04d}"
        
        # Extract the actual question from the DM response
        question_text = self._extract_question_text(dm_response)
        
        self.active_question = QuestionContext(
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            dm_prompt=dm_response,
            consequences_accept=consequences_accept,
            consequences_decline=consequences_decline,
            metadata=metadata or {}
        )
        
        self.is_active = True
        self.question_history.append(self.active_question)
        
        return self.active_question
    
    def _extract_question_text(self, dm_response: str) -> str:
        """
        Extract the key question from DM response.
        Usually the last sentence ending with '?'
        """
        sentences = dm_response.split('.')
        for sentence in reversed(sentences):
            if '?' in sentence:
                return sentence.strip()
        
        # Fallback: last 200 characters
        return dm_response[-200:].strip()
    
    def validate_response(self, player_input: str) -> PlayerResponse:
        """
        Validate and normalize player's response.
        
        Args:
            player_input: Raw player input
            
        Returns:
            Normalized PlayerResponse enum value
        """
        if not self.is_active or not self.active_question:
            return PlayerResponse.INVALID
        
        # Normalize input
        normalized = player_input.lower().strip()
        
        # Direct mapping check
        if normalized in self.RESPONSE_MAPPING:
            return self.RESPONSE_MAPPING[normalized]
        
        # Fuzzy matching for common phrases
        if any(word in normalized for word in ['accept', 'yes', 'agree', 'take', 'ok', 'sure']):
            return PlayerResponse.ACCEPT
        
        if any(word in normalized for word in ['decline', 'no', 'refuse', 'leave', 'pass', 'nope']):
            return PlayerResponse.DECLINE
        
        # No match found
        return PlayerResponse.INVALID
    
    def process_response(self, player_input: str) -> QuestionResponse:
        """
        Process player's response to the active question.
        
        Args:
            player_input: Player's raw input
            
        Returns:
            QuestionResponse object
        """
        if not self.is_active or not self.active_question:
            raise ValueError("No active question to respond to")
        
        validated = self.validate_response(player_input)
        
        response = QuestionResponse(
            question_id=self.active_question.question_id,
            response=validated,
            player_input=player_input,
            processed=True
        )
        
        self.response_history.append(response)
        
        # Deactivate if valid response
        if validated != PlayerResponse.INVALID:
            self.is_active = False
        
        return response
    
    def get_response_prompt(self) -> str:
        """
        Generate a prompt to guide the player's response.
        
        Returns:
            Formatted response prompt
        """
        if not self.is_active or not self.active_question:
            return ""
        
        q_type = self.active_question.question_type
        
        prompts = {
            QuestionType.ACCEPT_DECLINE: "📋 **Respond with:** Accept or Decline",
            QuestionType.YES_NO: "📋 **Respond with:** Yes or No",
            QuestionType.AGREE_REFUSE: "📋 **Respond with:** Agree or Refuse",
            QuestionType.TAKE_LEAVE: "📋 **Respond with:** Take or Leave",
        }
        
        base_prompt = prompts.get(q_type, "📋 **Respond with:** Accept or Decline")
        
        # Add consequences if available
        consequences = []
        if self.active_question.consequences_accept:
            consequences.append(f"✓ **Accept:** {self.active_question.consequences_accept}")
        if self.active_question.consequences_decline:
            consequences.append(f"✗ **Decline:** {self.active_question.consequences_decline}")
        
        if consequences:
            return f"{base_prompt}\n" + "\n".join(consequences)
        
        return base_prompt
    
    def get_invalid_response_message(self) -> str:
        """Get a helpful message when player gives invalid response"""
        if not self.active_question:
            return "No active question."
        
        q_type = self.active_question.question_type
        
        messages = {
            QuestionType.ACCEPT_DECLINE: "⚠️ Please respond with **Accept** or **Decline**.",
            QuestionType.YES_NO: "⚠️ Please respond with **Yes** or **No**.",
            QuestionType.AGREE_REFUSE: "⚠️ Please respond with **Agree** or **Refuse**.",
            QuestionType.TAKE_LEAVE: "⚠️ Please respond with **Take** or **Leave**.",
        }
        
        return messages.get(q_type, "⚠️ Please respond with **Accept** or **Decline**.")
    
    def clear_question(self):
        """Clear the active question state"""
        self.active_question = None
        self.is_active = False
    
    def get_statistics(self) -> Dict:
        """Get statistics about questions asked"""
        total_questions = len(self.question_history)
        total_responses = len(self.response_history)
        
        accepts = sum(1 for r in self.response_history if r.response == PlayerResponse.ACCEPT)
        declines = sum(1 for r in self.response_history if r.response == PlayerResponse.DECLINE)
        invalid = sum(1 for r in self.response_history if r.response == PlayerResponse.INVALID)
        
        return {
            'total_questions': total_questions,
            'total_responses': total_responses,
            'accepts': accepts,
            'declines': declines,
            'invalid_responses': invalid,
            'current_active': self.is_active,
            'acceptance_rate': accepts / total_responses if total_responses > 0 else 0
        }
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary for storage"""
        return {
            'is_active': self.is_active,
            'active_question': {
                'question_id': self.active_question.question_id,
                'question_text': self.active_question.question_text,
                'question_type': self.active_question.question_type.value,
                'dm_prompt': self.active_question.dm_prompt,
                'consequences_accept': self.active_question.consequences_accept,
                'consequences_decline': self.active_question.consequences_decline,
                'timestamp': self.active_question.timestamp,
                'metadata': self.active_question.metadata
            } if self.active_question else None,
            'question_counter': self._question_counter,
            'statistics': self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QuestioningState':
        """Deserialize from dictionary"""
        state = cls()
        state.is_active = data.get('is_active', False)
        state._question_counter = data.get('question_counter', 0)
        
        if data.get('active_question'):
            q_data = data['active_question']
            state.active_question = QuestionContext(
                question_id=q_data['question_id'],
                question_text=q_data['question_text'],
                question_type=QuestionType(q_data['question_type']),
                dm_prompt=q_data['dm_prompt'],
                consequences_accept=q_data.get('consequences_accept'),
                consequences_decline=q_data.get('consequences_decline'),
                timestamp=q_data.get('timestamp', ''),
                metadata=q_data.get('metadata', {})
            )
        
        return state


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def integrate_with_dm_response(
    dm_response: str,
    questioning_state: QuestioningState,
    auto_detect: bool = True
) -> tuple[str, bool]:
    """
    Integrate questioning state with DM response.
    
    Args:
        dm_response: DM's narration
        questioning_state: QuestioningState instance
        auto_detect: Automatically detect questions
        
    Returns:
        (formatted_response, is_question_active)
    """
    is_question = False
    
    if auto_detect:
        q_type = questioning_state.detect_question(dm_response)
        if q_type:
            questioning_state.activate_question(dm_response, question_type=q_type)
            is_question = True
    
    # Format response with prompt if question is active
    if questioning_state.is_active:
        response_prompt = questioning_state.get_response_prompt()
        formatted = f"{dm_response}\n\n---\n{response_prompt}"
        return formatted, True
    
    return dm_response, False


def handle_player_input(
    player_input: str,
    questioning_state: QuestioningState
) -> tuple[bool, Optional[QuestionResponse], Optional[str]]:
    """
    Handle player input in questioning state.
    
    Args:
        player_input: Player's raw input
        questioning_state: QuestioningState instance
        
    Returns:
        (is_valid, response_object, error_message)
    """
    if not questioning_state.is_active:
        return True, None, None  # Not in question state, proceed normally
    
    # Validate response
    validated = questioning_state.validate_response(player_input)
    
    if validated == PlayerResponse.INVALID:
        error_msg = questioning_state.get_invalid_response_message()
        return False, None, error_msg
    
    # Process valid response
    response = questioning_state.process_response(player_input)
    return True, response, None


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("QUESTIONING STATE - TEST SUITE")
    print("=" * 70)
    
    qs = QuestioningState()
    
    # Test 1: Detect questions
    print("\n📋 TEST 1: Question Detection")
    print("-" * 70)
    
    test_dm_responses = [
        "The mysterious stranger offers you a gleaming sword. Will you accept it?",
        "The goblin chieftain demands tribute. Do you agree to his terms?",
        "You find a cursed amulet. Do you take it or leave it?",
        "The wizard offers to teach you forbidden magic. Yes or no?",
        "You arrive at the tavern and see your party." # Not a question
    ]
    
    for dm_resp in test_dm_responses:
        detected = qs.detect_question(dm_resp)
        print(f"\nDM: {dm_resp[:60]}...")
        print(f"Detected: {detected.value if detected else 'No question detected'}")
    
    # Test 2: Activate question
    print("\n\n📋 TEST 2: Activate Question State")
    print("-" * 70)
    
    dm_response = "A hooded figure approaches. 'I have information about the dragon's lair,' he whispers. 'But it will cost you 100 gold. Do you accept my offer?'"
    
    question = qs.activate_question(
        dm_response=dm_response,
        consequences_accept="You learn the dragon's weakness",
        consequences_decline="You must find another way"
    )
    
    print(f"\n✓ Question activated:")
    print(f"  ID: {question.question_id}")
    print(f"  Type: {question.question_type.value}")
    print(f"  Question: {question.question_text}")
    print(f"\n{qs.get_response_prompt()}")
    
    # Test 3: Validate responses
    print("\n\n📋 TEST 3: Response Validation")
    print("-" * 70)
    
    test_inputs = [
        "accept",
        "yes",
        "I accept the offer",
        "decline",
        "no thanks",
        "maybe later",  # Invalid
        "what about 50 gold?",  # Invalid
        "ok"
    ]
    
    for test_input in test_inputs:
        validated = qs.validate_response(test_input)
        print(f"\nPlayer: '{test_input}' → {validated.value}")
    
    # Test 4: Process valid response
    print("\n\n📋 TEST 4: Process Response")
    print("-" * 70)
    
    player_input = "I accept"
    response = qs.process_response(player_input)
    
    print(f"\nPlayer input: '{player_input}'")
    print(f"✓ Response recorded:")
    print(f"  Question ID: {response.question_id}")
    print(f"  Response: {response.response.value}")
    print(f"  Timestamp: {response.timestamp}")
    print(f"  State active: {qs.is_active}")
    
    # Test 5: Integration helper
    print("\n\n📋 TEST 5: Integration Helper")
    print("-" * 70)
    
    qs2 = QuestioningState()
    dm_resp = "The dragon offers a truce. Will you accept or fight?"
    
    formatted, is_question = integrate_with_dm_response(dm_resp, qs2)
    
    print("\nDM Response:")
    print(formatted)
    print(f"\nQuestion Active: {is_question}")
    
    # Test invalid response handling
    is_valid, resp, error = handle_player_input("maybe", qs2)
    print(f"\nPlayer: 'maybe'")
    print(f"Valid: {is_valid}")
    print(f"Error: {error}")
    
    # Test valid response
    is_valid, resp, error = handle_player_input("accept", qs2)
    print(f"\nPlayer: 'accept'")
    print(f"Valid: {is_valid}")
    print(f"Response: {resp.response.value if resp else None}")
    
    # Test 6: Statistics
    print("\n\n📋 TEST 6: Statistics")
    print("-" * 70)
    
    stats = qs.get_statistics()
    print("\n" + "Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS COMPLETED")
    print("=" * 70)