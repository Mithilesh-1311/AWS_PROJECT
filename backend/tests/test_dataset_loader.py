"""
Tests for DatasetLoader
"""
import pytest
from app.data.dataset_loader import DatasetLoader
from app.core.config import DATASET_ROOT, EXPECTED_SUBJECTS

@pytest.fixture
def loader():
    if not DATASET_ROOT or not DATASET_ROOT.exists():
        pytest.skip("Dataset root not found")
    return DatasetLoader(DATASET_ROOT)

def test_loader_init(loader):
    assert loader is not None
    assert len(loader.subject_ids) == 14
    assert loader.subject_ids[0] == "S1"
    assert loader.subject_ids[-1] == "S14"

def test_subject_metadata(loader):
    meta = loader.get_subject_metadata("S1")
    assert meta.subject_id == "S1"
    assert meta.n_channels == 16
    assert meta.n_samples > 290000
    assert meta.n_trials == 288
    assert 0.05 <= meta.pd <= 0.08
    assert 0.50 <= meta.dist_screen <= 0.60

def test_get_control_signal(loader):
    cs = loader.get_control_signal("S1")
    assert cs.ndim == 1
    assert set(cs).issubset({1, 2, 3, 30})

def test_get_target_ga_stream(loader):
    tga = loader.get_target_ga_stream("S1")
    assert tga.ndim == 2
    assert tga.shape[0] == 2
    assert tga.shape[1] > 290000
