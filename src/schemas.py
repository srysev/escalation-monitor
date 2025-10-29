# src/schemas.py
from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field

class DimensionScore(BaseModel):
    """Score for a single dimension"""
    score: float = Field(..., ge=1.0, le=10.0, description="Dimension score from 1.0 to 10.0")
    rationale: str = Field(..., description="Neutral explanation for the score")

class OverallAssessment(BaseModel):
    """Overall escalation assessment focused on synthesis and neutrality"""
    overall_score: float = Field(..., ge=1.0, le=10.0, description="Overall escalation score")
    situation_summary: str = Field(..., description="Neutral summary of current situation using markdown formatting for structure")