from dataclasses import dataclass
from typing import Any, Literal, Optional

from agents.agent import Agent


@dataclass
class ScoringConfig:
    ground_truth: Any = None  # For literal checks
    criteria: Optional[str] = None  # For model graders
    type: Optional[Literal['tool_name', 'tool_argument', 'handoff', 'model_graded']] = None

@dataclass
class TestCase:
    name: str
    scoring_config: ScoringConfig
    scenario: str # step by step scenario: 1. user says X, 2. agent does Y...or Given-When-Then
    agent_to_test: Agent
