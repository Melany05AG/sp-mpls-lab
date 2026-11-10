"""Pruebas del plano de control: IGP, MPLS/LDP y BGP."""
import pytest

from conftest import wait_until
import lab

LOOPBACKS = {
    "p1": ("10.255.0.1", "2001:db8:ffff::1"),
    "p2": ("10.255.0.2", "2001:db8:ffff::2"),
    "pe1": ("10.255.0.11", "2001:db8:ffff::11"),
    "pe2": ("10.255.0.12", "2001:db8:ffff::12"),
    "pe3": ("10.255.0.13", "2001:db8:ffff::13"),
}

@pytest.mark.parametrize("node,expected", lab.EXPECTED_ISIS.items())
def test_cp01_isis_adjacencies(lab_mod, node, expected):
    """CP-01: cada nodo del nucleo tiene todas sus adyacencias IS-IS en Up."""
    assert wait_until(lambda: lab.isis_adjacencies_up(node) == expected), \
        f"{node}: {lab.isis_adjacencies_up(node)} adyacencias, se esperaban {expected}"


@pytest.mark.parametrize("node", lab.PE + lab.CORE)
def test_cp02_loopbacks_in_igp(lab_mod, node):
    """CP-02: todas las loopbacks (IPv4 e IPv6) se aprenden por IS-IS."""
    own = LOOPBACKS[node]
    v4 = lab.vtysh(node, "show ip route isis")
    v6 = lab.vtysh(node, "show ipv6 route isis")
    for other, (lo4, lo6) in LOOPBACKS.items():
        if (lo4, lo6) == own:
            continue
        assert f"{lo4}/32" in v4, f"{node} no aprende {lo4}/32 de {other}"
        assert f"{lo6}/128" in v6, f"{node} no aprende {lo6}/128 de {other}"


@pytest.mark.parametrize("node,expected", lab.EXPECTED_LDP.items())
def test_cp03_ldp_sessions(lab_mod, node, expected):
    """CP-03: sesiones LDP OPERATIONAL en todos los enlaces del nucleo."""
    assert wait_until(lambda: lab.ldp_sessions_operational(node) == expected)


@pytest.mark.parametrize("remote", ["10.255.0.12", "10.255.0.13"])
def test_cp04_lsp_to_remote_pe(lab_mod, remote):
    """CP-04: PE1 tiene etiqueta MPLS (LSP) hacia las loopbacks de los PE remotos."""
    out = lab.vtysh("pe1", f"show mpls ldp binding {remote}/32")
    assert remote in out and "yes" in out.lower(), out


@pytest.mark.parametrize(
    "node,command,expected",
    [(n, c, e) for n, checks in lab.EXPECTED_BGP.items() for c, e in checks],
)
def test_cp05_bgp_sessions(lab_mod, node, command, expected):
    """CP-05: sesiones BGP (iBGP al RR, eBGP PE-CE v4/v6) en Established."""
    assert wait_until(lambda: lab.bgp_established(node, command) == expected), \
        f"{node} '{command}': {lab.bgp_peers(node, command)}"


def test_cp06_p2_is_bgp_free(lab_mod):
    """CP-06: P2 no ejecuta BGP (nucleo libre de BGP gracias a MPLS)."""
    out = lab.vtysh("p2", "show running-config")
    assert "router bgp" not in out


@pytest.mark.parametrize("node", ["pe1", "pe3"])
def test_cp07_ospf_pe_ce(lab_mod, node):
    """CP-07: adyacencia OSPF PE-CE Full en la VRF CUST-A."""
    assert wait_until(lambda: lab.ospf_full(node, "CUST-A") == 1)


def test_cp08_vpn_routes_carry_labels(lab_mod):
    """CP-08: la ruta del sitio remoto en la VRF tiene etiqueta VPN (L3VPN sobre MPLS)."""
    out = wait_until(lambda: lab.vtysh("pe1", "show ip route vrf CUST-A 10.10.30.0/24"))
    assert "10.10.30.0/24" in out and "label" in out.lower(), out


def test_cp09_private_lan_not_advertised(lab_mod):
    """CP-09: la LAN privada de CUST-B (192.168.50.0/24) no se filtra a la VPN."""
    out = lab.vtysh("pe1", "show bgp vrf CUST-B ipv4 unicast")
    assert "192.168.50.0" not in out
    assert "198.51.100.1/32" in out
