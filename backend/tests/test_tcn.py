import pytest
import numpy as np

torch = pytest.importorskip('torch')
from app.models.tcn import TinyTCN


@pytest.mark.parametrize('config,parameter_count', [({}, 4880), ({'hidden':32, 'dilations':[1,2,4,8]}, 11144)])
def test_tcn_prefix_padding_and_roundtrip(tmp_path, config, parameter_count):
    torch.manual_seed(42)
    model = TinyTCN(**config).eval()
    assert sum(p.numel() for p in model.parameters()) == parameter_count
    x = torch.randn(2, 16, 26)
    changed = x.clone()
    changed[:, :, 13:] = 999
    lengths = torch.tensor([13, 13])
    with torch.no_grad():
        expected = model(x, lengths)
        assert torch.equal(expected, model(changed, lengths))
        assert torch.equal(model.encoder(x)[:, :, :13], model.encoder(changed)[:, :, :13])
        torch.save(model.state_dict(), tmp_path / 'model.pt')
        restored = TinyTCN(**config).eval()
        restored.load_state_dict(torch.load(tmp_path / 'model.pt', weights_only=True))
        assert torch.equal(expected, restored(x, lengths))
        assert np.isfinite(expected.numpy()).all()
    with pytest.raises(ValueError):
        model(x, torch.tensor([0, 27]))


def test_full_window_architecture_can_use_first_of_26_samples():
    x = torch.zeros(1, 16, 26)
    changed = x.clone()
    changed[:, :, 0] = 1
    lengths = torch.tensor([26])
    with torch.no_grad():
        for config, observes_first_sample in [({}, False), ({'hidden':32, 'dilations':[1,2,4,8]}, True)]:
            model = TinyTCN(**config).eval()
            for parameter in model.parameters():
                parameter.fill_(.01)
            assert (not torch.equal(model(x, lengths), model(changed, lengths))) == observes_first_sample
