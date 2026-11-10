"""Pruebas de servicio extremo a extremo: L3VPN, L2VPN (EVPN), NAT, IPv6, VLAN/STP."""
import pytest

from conftest import wait_until
import lab


# ------------------------------------------------------------ L3VPN CUST-A
@pytest.mark.parametrize("src,dst", [
    ("h-a10", "10.10.30.10"),   # sitio 1 VLAN 10 -> sitio 2 (via L3VPN)
    ("h-a20", "10.10.30.10"),   # sitio 1 VLAN 20 -> sitio 2 (via L3VPN)
    ("h-a30", "10.10.10.10"),
])
def test_sv01_l3vpn_cust_a(lab_mod, src, dst):
    """SV-01: conectividad entre sitios de CUST-A sobre la L3VPN."""
    assert wait_until(lambda: lab.ping(src, dst), timeout=90)


# ------------------------------------------------------------ VLAN / STP
def test_sv02_inter_vlan_routing(lab_mod):
    """SV-02: enrutamiento entre VLAN 10 y 20 en CE-A1 (router-on-a-stick)."""
    assert wait_until(lambda: lab.ping("h-a10", "10.10.20.10"), timeout=90)


def test_sv03_stp_blocks_redundant_link(lab_mod):
    """SV-03: con dos troncales SW-A1<->SW-A2, STP deja una en forwarding y bloquea la otra."""
    states = wait_until(
        lambda: (s := lab.stp_port_states("sw-a2", ["eth1", "eth2"]))
        and sorted(s.values()) == ["blocking", "forwarding"] and s,
        timeout=60,
    )
    assert isinstance(states, dict), f"estados STP: {lab.stp_port_states('sw-a2', ['eth1', 'eth2'])}"


def test_sv04_stp_root_bridge(lab_mod):
    """SV-04: SW-A1 (prioridad 4096) es el puente raiz."""
    out = lab.sh("sw-a1", "cat /sys/class/net/br0/bridge/root_id /sys/class/net/br0/bridge/bridge_id").stdout.split()
    assert len(out) == 2 and out[0] == out[1], out


# ------------------------------------------------------------ L3VPN CUST-B + NAT + IPv6
def test_sv05_l3vpn_cust_b_with_nat(lab_mod):
    """SV-05: H-B1 (192.168.50.10, privada) llega a H-B2 gracias al NAT de CE-B1."""
    assert wait_until(lambda: lab.ping("h-b1", "198.51.100.130"), timeout=90)
    counters = lab.sh("ce-b1", "iptables -t nat -L POSTROUTING -v -n -x").stdout
    snat = [line for line in counters.splitlines() if "SNAT" in line]
    assert snat and int(snat[0].split()[0]) > 0, counters


def test_sv06_private_address_not_reachable(lab_mod):
    """SV-06: la direccion privada no es alcanzable desde el otro sitio (no se enruta)."""
    assert not lab.ping("h-b2", "192.168.50.10", count=2)


def test_sv07_ipv6_end_to_end(lab_mod):
    """SV-07: IPv6 extremo a extremo en CUST-B (VPNv6 / 6VPE), sin NAT."""
    assert wait_until(lambda: lab.ping("h-b1", "2001:db8:b2::10", v6=True), timeout=90)


# ------------------------------------------------------------ Aislamiento entre VRF
@pytest.mark.parametrize("src,dst", [("h-a10", "198.51.100.130"), ("h-b2", "10.10.30.10")])
def test_sv08_vrf_isolation(lab_mod, src, dst):
    """SV-08: los clientes A y B estan aislados entre si."""
    assert not lab.ping(src, dst, count=2)


# ------------------------------------------------------------ L2VPN EVPN-VXLAN CUST-C
def test_sv09_evpn_remote_vtep(lab_mod):
    """SV-09: PE2 descubre a PE3 como VTEP remoto del VNI 30030 por BGP EVPN."""
    out = wait_until(lambda: (o := lab.vtysh("pe2", "show evpn vni 30030")) and "10.255.0.13" in o and o)
    assert out and "10.255.0.13" in out


def test_sv10_evpn_l2_reachability(lab_mod):
    """SV-10: H-C1 y H-C2 comparten el segmento 10.30.0.0/24 sobre la L2VPN."""
    assert wait_until(lambda: lab.ping("h-c1", "10.30.0.2"), timeout=90)
    macs = lab.vtysh("pe2", "show evpn mac vni 30030")
    assert "remote" in macs.lower(), macs
