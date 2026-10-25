import pytest
import numpy as np

torch = pytest.importorskip('torch')
from app.models.tcn import TinyTCN


def test_tcn_prefix_padding_and_roundtrip(tmp_path):
    torch.manual_seed(42)
    model = TinyTCN().eval()
    x = torch.randn(2, 16, 26)
    changed = x.clone()
    changed[:, :, 13:] = 999
    lengths = torch.tensor([13, 13])
    with torch.no_grad():
        expected = model(x, lengths)
        assert torch.equal(expected, model(changed, lengths))
        assert torch.equal(model.encoder(x)[:, :, :13], model.encoder(changed)[:, :, :13])
        torch.save(model.state_dict(), tmp_path / 'model.pt')
        restored = TinyTCN().eval()
        restored.load_state_dict(torch.load(tmp_path / 'model.pt', weights_only=True))
        assert torch.equal(expected, restored(x, lengths))
        assert np.isfinite(expected.numpy()).all()
    with pytest.raises(ValueError):
        model(x, torch.tensor([0, 27]))
