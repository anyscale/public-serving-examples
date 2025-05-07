from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class TextRequest(BaseModel):
    """Base request model for text-based NLP operations."""

    text: str = Field(..., min_length=1, description="The input text to analyze")
    language: str = Field("en", description="ISO language code")
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Additional options for processing"
    )

    @validator("text")
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v


class ClassificationRequest(TextRequest):
    """Request model for text classification."""

    labels: List[str] = Field(
        ..., min_items=1, description="Possible categories for classification"
    )
    multi_label: bool = Field(False, description="Whether to allow multiple labels")


class SentimentResponse(BaseModel):
    """Response model for sentiment analysis."""

    text: str = Field(..., description="The input text")
    sentiment: str = Field(
        ..., description="Detected sentiment (positive, negative, neutral)"
    )
    score: float = Field(..., ge=0, le=1, description="Confidence score")
    language: str = Field(..., description="Detected or specified language")
    processing_time: float = Field(..., description="Processing time in seconds")


class ClassificationResponse(BaseModel):
    """Response model for text classification."""

    text: str = Field(..., description="The input text")
    labels: List[Dict[str, Union[str, float]]] = Field(
        ..., description="List of labels with scores"
    )
    processing_time: float = Field(..., description="Processing time in seconds")


class EntityType(str, Enum):
    """Types of named entities."""

    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "LOC"
    DATE = "DATE"
    TIME = "TIME"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    FACILITY = "FACILITY"
    PRODUCT = "PRODUCT"
    EVENT = "EVENT"
    WORK_OF_ART = "WORK_OF_ART"
    LAW = "LAW"
    LANGUAGE = "LANGUAGE"
    OTHER = "O"


class Entity(BaseModel):
    """Model for a named entity."""

    text: str = Field(..., description="The entity text")
    start: int = Field(..., description="Start position in the text")
    end: int = Field(..., description="End position in the text")
    type: str = Field(..., description="Entity type")
    score: float = Field(..., ge=0, le=1, description="Confidence score")


class EntityResponse(BaseModel):
    """Response model for named entity recognition."""

    text: str = Field(..., description="The input text")
    entities: List[Entity] = Field(..., description="List of recognized entities")
    processing_time: float = Field(..., description="Processing time in seconds")


class SummarizationRequest(TextRequest):
    """Request model for text summarization."""

    max_length: int = Field(
        100, ge=10, description="Maximum length of summary in tokens"
    )
    min_length: int = Field(30, ge=5, description="Minimum length of summary in tokens")
    do_sample: bool = Field(False, description="Whether to use sampling")


class SummarizationResponse(BaseModel):
    """Response model for text summarization."""

    original_text: str = Field(..., description="The original input text")
    summary: str = Field(..., description="Generated summary")
    processing_time: float = Field(..., description="Processing time in seconds")


class TranslationRequest(TextRequest):
    """Request model for language translation."""

    source_lang: str = Field("en", description="Source language code")
    target_lang: str = Field("fr", description="Target language code")


class TranslationResponse(BaseModel):
    """Response model for language translation."""

    original_text: str = Field(..., description="The original input text")
    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")
    processing_time: float = Field(..., description="Processing time in seconds")


class ModelInfo(BaseModel):
    """Information about an NLP model."""

    name: str = Field(..., description="Model name")
    task: str = Field(..., description="NLP task")
    languages: List[str] = Field(..., description="Supported languages")
    description: Optional[str] = Field(None, description="Model description")
    performance_metrics: Optional[Dict[str, float]] = Field(
        None, description="Performance metrics"
    )


class HistoryItem(BaseModel):
    """Model for a history item."""

    request_id: str = Field(..., description="Unique request ID")
    user_id: str = Field(..., description="User ID")
    endpoint: str = Field(..., description="API endpoint")
    request_data: Dict[str, Any] = Field(..., description="Request data")
    timestamp: float = Field(..., description="Unix timestamp")


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error description")
    error_type: Optional[str] = Field(None, description="Error type")
    error_code: Optional[int] = Field(None, description="Error code")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    models: Dict[str, bool] = Field(..., description="Model availability")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
