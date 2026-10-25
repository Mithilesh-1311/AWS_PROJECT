"""Versioned HTTP response contracts; experiment-specific config stays extensible."""
from typing import Literal
from pydantic import BaseModel, ConfigDict


class WindowResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
    requested_ms: float
    n_samples: int
    sample_budget_ms: float
    sample_span_ms: float
    crossing_sample: int | None
    confirmation_sample: int | None
    ready_sample: int
    cue_to_decision_ms: float
    calibration_samples: int
    preprocessing_version: str
    alignment: str


class PredictedResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
    state: Literal['predicted']
    model_id: str
    experiment_id: str
    predicted_class: int
    predicted_direction: str
    scores: list[float]
    score_semantics: str
    class_names: list[str]
    window: WindowResponse
    feature_ms: float
    inference_ms: float
    warnings: list[str]


class AbstainedResponse(BaseModel):
    state: Literal['abstained']
    reason: str
    model_id: str
    subject_id: str
    trial_id: int


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
    model_id: str
    experiment_id: str
    window_ms: float
    alignment: str
    preprocessing_version: str
    feature_version: str
    class_names: list[str]
    class_order: list[int]
    score_semantics: str
    ready: bool


class RegistryResponse(BaseModel):
    models: list[ModelResponse]
    active_model_id: str | None


class JobResponse(BaseModel):
    id: str
    state: Literal['queued', 'running', 'succeeded', 'failed', 'cancelled']
    config: dict
    progress: dict
    result: dict | None
    error: dict | None
    created: float
    updated: float


class JobsResponse(BaseModel):
    jobs: list[JobResponse]
    worker_ready: bool
