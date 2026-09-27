import pytest

from src.utils.auto_shutdown import AutoShutdown
from src.utils.monitoring import ServerMonitor


@pytest.mark.parametrize("feature", [AutoShutdown, ServerMonitor])
def test_disabled_features_cannot_start_background_services(feature):
    with pytest.raises(NotImplementedError):
        feature()
