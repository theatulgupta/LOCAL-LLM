"""Pydantic models for request/response validation"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class QueryRequest(BaseModel):
    """Request model for LLM query"""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="The prompt to send to the LLM"
    )
    model: Optional[str] = Field(
        default="qwen2.5-coder:7b",
        description="Ollama model to use"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for generation (0-2)"
    )
    top_p: Optional[float] = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-p sampling parameter"
    )
    top_k: Optional[int] = Field(
        default=40,
        ge=0,
        description="Top-k sampling parameter"
    )
    num_predict: Optional[int] = Field(
        default=128,
        ge=1,
        description="Number of tokens to generate"
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream the response"
    )
    use_rag: Optional[bool] = Field(
        default=True,
        description="Whether to enrich the prompt with local lab context"
    )
    rag_top_k: Optional[int] = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of local lab chunks to include"
    )

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate and sanitize prompt"""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v.strip()


class QueryResponse(BaseModel):
    """Response model for LLM query"""

    response: str = Field(..., description="Generated response from the LLM")
    model: str = Field(..., description="Model used")
    prompt: str = Field(..., description="Original prompt")
    requested_model: Optional[str] = Field(
        default=None,
        description="Model requested by the client"
    )
    context_used: bool = Field(
        default=False,
        description="Whether local RAG context was injected"
    )
    context_sources: List["RagSource"] = Field(
        default_factory=list,
        description="Matched local context sources"
    )
    total_duration: Optional[float] = Field(
        default=None,
        description="Total duration in nanoseconds"
    )
    load_duration: Optional[float] = Field(
        default=None,
        description="Model load duration in nanoseconds"
    )
    rag: Optional[dict] = Field(
        default=None,
        description="RAG metadata (enabled, sources_count, corpus_path, etc.)"
    )


class StreamingQueryResponse(BaseModel):
    """Response model for streaming LLM query"""

    token: str = Field(..., description="Generated token")
    model: str = Field(..., description="Model used")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Server status")
    version: str = Field(..., description="API version")
    ollama_status: str = Field(..., description="Ollama server status")


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )
    status_code: int = Field(..., description="HTTP status code")


class ModelInfo(BaseModel):
    """Information about available models"""

    name: str
    description: Optional[str] = None
    size: Optional[str] = None


class AvailableModelsResponse(BaseModel):
    """Response with list of available models"""

    models: List[str] = Field(..., description="List of available model names")
    count: int = Field(..., description="Number of available models")


class RagSource(BaseModel):
    """Matched local note or notebook chunk."""

    source_path: str = Field(..., description="Relative source file path")
    chunk_index: int = Field(..., description="Chunk index within the source")
    score: float = Field(..., description="Similarity score")
    snippet: str = Field(..., description="Matched text snippet")
    cell_type: Optional[str] = Field(default=None, description="Notebook cell type")
    cell_id: Optional[str] = Field(default=None, description="Notebook cell id")


class RagSearchRequest(BaseModel):
    """Request model for searching the local RAG corpus."""

    question: str = Field(..., min_length=1, max_length=4096)
    top_k: Optional[int] = Field(default=3, ge=1, le=10)


class RagSearchResponse(BaseModel):
    """Response from the local RAG search endpoint."""

    question: str
    context: str
    sources: List[RagSource]
    enabled: bool
    indexed_files: int
    indexed_chunks: int
    corpus_path: str


class RagStatusResponse(BaseModel):
    """RAG index status."""

    enabled: bool
    ready: bool
    corpus_path: str
    indexed_files: int
    indexed_chunks: int


QueryResponse.model_rebuild()
