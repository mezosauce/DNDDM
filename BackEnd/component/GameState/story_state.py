#!/usr/bin/env python3
"""
•	Story State:
o	Input:
    	Characters.Json
    	Campaign.Json
    	Session Notes
    	If {Game_State_INIT}
        •	INIT Story Prompt
    	If {Next_Game_State == Combat State}: 
        •	SRD_Cycle/Monsters.Index.MD
        •	Combat Prep Prompt
    	If {Next_Game_State == Questoning State}:
        •	Questioning State Prompt
    	If {Next_Game_State == Dice Roll State}:
        •	Dice Roll Situation Prompt
    	If {Last_Game_State == Combat State}:
        •	Post Combat Prompt
    	If {Last_Game_State == Questioning State}:
        •	Post Questioning Prompt
    	If {Last_Game_State == Dice Roll State}:
        •	Post Dice Roll Prompt
    	If {Next_Game_State == END:
        •	Story Wrap up Prompt
o	Output:
    	If {Game_State_INIT} 
        •	INIT Story Dialogue
    	If {Next_Game_State == Combat State}:
        •	Give Chosen <Monster> Dialogue 
        •	Provide <Monster> Base Stats <Scaled>
    	If {Next_Game_State == Questoning State}:
        •	Provide <Situation> with only options to either Accept/ Decline
    	If {Next_Game_State == Dice Roll State}:
        •	Provide <Situation> Dialogue
        •	Provide type of Dice the Player has to roll
    	If {Last_Game_State == Combat State}:
        •	Post Combat Dialogue 
    	If {Last_Game_State == Questioning State}:
        •	Post Questioning Dialogue
    	If {Last_Game_State == Dice Roll State}:
        •	Post Dice Roll Dialogue
    	If {Next_Game_State == END:
        •	Story Wrap up Dialogue

"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable
from datetime import datetime

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]  # Goes up 1 levels to DNDDM folder
sys.path.insert(0, str(project_root))

from BackEnd.prompts import campaign_init_prompt, pre_combat_prompt, post_combat_prompt, pre_diceroll_prompt, post_diceroll_prompt, pre_question_prompt, post_question_prompt, wrapup_prompt
from GameState.combat_state import CombatState
from GameState.dice_state import DiceRollState
from GameState.question_state import QuestioningState

