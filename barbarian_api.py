from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Head.Class.barbarian import Barbarian
rffffffffffffffffffdtgfrrrrrrrrrrrrrrrrrr
app = FastAPI(title="Barbarian API")

# ---------------------------
# CORS (allow frontend access)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# In-memory database
# ---------------------------
BARBARIANS = {}


# ---------------------------
# Pydantic Models
# ---------------------------
class CreateBarbarianRequest(BaseModel):
    level: int = 1
    stats: dict = None
    race: str = "Human"
    background: str = ""


class UpdateStatsRequest(BaseModel):
    stats: dict


class SetLevelRequest(BaseModel):
    level: int


# ---------------------------
# ROUTES
# ---------------------------

@app.get("/docs")
def root():
    return {
        "status": "online",
        "message": "Barbarian FastAPI running",
        "endpoints": [
            "/api/barbarian/{name}",
            "/api/barbarian/{name}/create",
            "/api/barbarian/{name}/enter_rage",
            "/api/barbarian/{name}/end_rage",
            "/api/barbarian/{name}/long_rest",
            "/api/barbarian/{name}/update_stats",
            "/api/barbarian/{name}/set_level",
        ],
    }


@app.get("/api/barbarian/{name}")
def get_barbarian(name: str):
    name = name.lower()
    if name not in BARBARIANS:
        raise HTTPException(status_code=404, detail="Character not found")

    return BARBARIANS[name].get_character_sheet()


@app.post("/api/barbarian/{name}/create")
def create_barbarian(name: str, request: CreateBarbarianRequest):
    name = name.lower()

    stats = request.stats or {
        "strength": 15,
        "dexterity": 13,
        "constitution": 14,
        "intelligence": 10,
        "wisdom": 12,
        "charisma": 8
    }

    bar = Barbarian(
        name=name,
        race=request.race,
        background=request.background,
        level=request.level,
        stats=stats
    )

    BARBARIANS[name] = bar

    return {"status": "created", "sheet": bar.get_character_sheet()}


@app.post("/api/barbarian/{name}/enter_rage")
def enter_rage(name: str):
    name = name.lower()

    if name not in BARBARIANS:
        raise HTTPException(status_code=404, detail="Character not found")

    success = BARBARIANS[name].enter_rage()

    return {"success": success, "sheet": BARBARIANS[name].get_character_sheet()}


@app.post("/api/barbarian/{name}/end_rage")
def end_rage(name: str):
    name = name.lower()

    if name not in BARBARIANS:
        raise HTTPException(status_code=404, detail="Character not found")

    BARBARIANS[name].end_rage()

    return {"status": "rage_ended", "sheet": BARBARIANS[name].get_character_sheet()}


@app.post("/api/barbarian/{name}/long_rest")
def long_rest(name: str):
    name = name.lower()

    if name not in BARBARIANS:
        raise HTTPException(status_code=404, detail="Character not found")

    BARBARIANS[name].long_rest()

    return {"status": "long_rest", "sheet": BARBARIANS[name].get_character_sheet()}


@app.post("/api/barbarian/{name}/update_stats")
def update_stats(name: str, request: UpdateStatsRequest):
    name = name.lower()

    if name not in BARBARIANS:
        raise HTTPException(status_code=404, detail="Character not found")

    BARBARIANS[name].stats.update(request.stats)
    BARBARIANS[name].calculate_unarmored_defense()

    return {"status": "stats_updated", "sheet": BARBARIANS[name].get_character_sheet()}


@app.post("/api/barbarian/{name}/set_level")
def set_level(name: str, request: SetLevelRequest):
    name = name.lower()

    if name not in BARBARIANS:
        raise HTTPException(status_code=404, detail="Character not found")

    target = request.level

    while BARBARIANS[name].level < target:
        BARBARIANS[name].level_up()

    return {"status": "level_updated", "sheet": BARBARIANS[name].get_character_sheet()}
