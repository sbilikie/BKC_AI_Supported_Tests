import pytest
from mfd_bkc_logic.features.system_tests.mev_bkc_bc import MevBkcBC
from mfd_bkc_logic.framework_logger import get_logger

log = get_logger()


@pytest.fixture(scope="class")
def bkc_base(request, test_config, topology_config):
    """
    Create MevBkcBC object, execute prepare on it
    This class object ("bkc_base") will be used in test method
    """
    bkc_base = MevBkcBC(test_config, topology_config)
    bkc_base.prepare()
    request.cls.bkc_base = bkc_base
    yield
    bkc_base.cleanup()


@pytest.mark.usefixtures("bkc_base")
class TestPlatform:
    """
    Check if layout of the ipu sdk directories is correct
    """

    @pytest.mark.simics
    def test_mev_system_tests_ipu_sdk_directory_layout(self):
        log.info(f"Check if layout of the ipu sdk directories is correct")
        platform = PLATFORM["client"]
        topology = self.bkc_base.topology_config_on_complexes[platform.name]
        platform = Platform(
            get_platform_terminal(self.bkc_base.config, topology, platform)
        )
        if platform.system_running_status():
            assert platform.verify_build_completness()
