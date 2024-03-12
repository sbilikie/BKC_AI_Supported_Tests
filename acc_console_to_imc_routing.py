import pytest
from mfd_bkc_logic.features.system_tests.utils import (
    get_ip_and_mask,
    get_network_interface,
    get_proper_config_section,
)
from mfd_bkc_logic.features.system_tests.consts import (
    PLATFORM,
    get_const_iface_plat,
    plat_iface,
    PLAT_WO_MEV_CONFIG,
)
from mfd_bkc_logic.features.system_tests.mev_bkc_multi_lan_bc import MevMultiLanDriverBC
from mfd_bkc_logic.utils import load_pytest_config, load_pytest_topology_config, dotdict
from mfd_bkc_logic.framework_logger import get_logger

log = get_logger()


def get_params():
    """
    Create test params with test cases names
    @return: list of params
    """
    config = load_pytest_config()
    topology_config = load_pytest_topology_config()
    mev_plat_ifaces = []
    mev_suts = []
    for config_platform in topology_config.hosts:
        config_platform = dotdict(config_platform)
        if config_platform.name.upper() in PLAT_WO_MEV_CONFIG:
            continue
        platform = PLATFORM[config_platform.name.upper()]
        platform_config = get_proper_config_section(config, platform)
        platform_network_interfaces = config_platform.get("network_interfaces")
        if platform_network_interfaces:
            mev_suts.append(platform_network_interfaces)
        for idx in range(len(platform_network_interfaces)):
            if config.general.pf_number == 1:
                idx = platform_config.vport_id
            const_iface = get_const_iface_plat(idx)
            network_interface = dotdict(
                get_network_interface(
                    network_interfaces=platform_network_interfaces,
                    interface_index=idx,
                )
            )
            mev_ipv4, mev_ipv4_mask = get_ip_and_mask(ips=network_interface.ips)
            mev_ipv6, mev_ipv6_mask = get_ip_and_mask(
                ips=network_interface.ips, v6=True
            )
            new_plat_ifaces = plat_iface(
                plat=platform,
                iface=None,
                iface_mac=None,
                ipv4=mev_ipv4,
                ipv4_mask=mev_ipv4_mask,
                ipv6=mev_ipv6,
                ipv6_mask=mev_ipv6_mask,
                vsi=None,
                const_iface=const_iface,
                netns=const_iface,
                terminal=None,
            )
            mev_plat_ifaces.append(new_plat_ifaces)

    return [
        pytest.param(
            mev_plat_iface,
            id=f"{mev_plat_iface.const_iface}_{mev_plat_iface.plat.name}",
        )
        for mev_plat_iface in mev_plat_ifaces
    ]


@pytest.fixture(scope="class")
def mev_multilan_driver_bc(request, test_config, topology_config):
    """
    Create MevMultiLanDriverBC object, execute prepare on it
    This class object ("MevMultiLanDriverBC") will be used in test method
    """
    mev_multilan_driver_bc = MevMultiLanDriverBC(test_config, topology_config)
    request.cls.mev_multilan_driver_bc = mev_multilan_driver_bc
    request.addfinalizer(mev_multilan_driver_bc.cleanup)

    mev_multilan_driver_bc.prepare()
    yield


@pytest.mark.usefixtures("mev_multilan_driver_bc")
class TestConnectionRouting:
    """
    Test class to check presence of idpf interfaces after loading
    """

    @pytest.mark.hw
    @pytest.mark.simics
    @pytest.mark.bat
    @pytest.mark.parametrize("mev_plat_iface", get_params())
    def test_mev_system_tests_presence_check_(self, mev_plat_iface):
        driver = self.mev_multilan_driver_bc.drivers[mev_plat_iface.plat]
        topology = self.mev_multilan_driver_bc.topology_config_on_complexes[
            mev_plat_iface.plat.name
        ]
        # This is actually going to check not only the serial but also the idpf presence, although for poc it's ok
        assert driver.is_working(topology)
