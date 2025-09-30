# src/schemas.py
from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field

class DimensionScore(BaseModel):
    """Score for a single dimension"""
    score: float = Field(..., ge=1.0, le=10.0, description="Dimension score from 1.0 to 10.0")
    rationale: str = Field(..., description="Neutral explanation for the score")

class DimensionReview(BaseModel):
    """Reviewed dimension with name"""
    name: str = Field(..., description="Dimension name")
    score: float = Field(..., ge=1.0, le=10.0, description="Possibly adjusted dimension score")
    rationale: str = Field(..., description="Neutral, reviewed explanation")

class OverallAssessment(BaseModel):
    """Overall escalation assessment with reviewed dimensions"""
    overall_score: float = Field(..., ge=1.0, le=10.0, description="Overall escalation score")
    situation_summary: str = Field(..., description="Neutral summary of current situation  using markdown formatting for structure")
    dimensions: List[DimensionReview] = Field(..., max_length=5, description="Reviewed dimension scores")