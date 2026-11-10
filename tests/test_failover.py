"""Pruebas de resiliencia (fallas simuladas). Ejecutar con: pytest -m failover

Cada prueba provoca una falla, valida que el servicio se recupere por la ruta
alterna y restaura el enlace al final, aunque la prueba falle.
"""
import time

import pytest

from conftest import wait_until
import lab

pytestmark = pytest.mark.failover


def set_link(node: str, iface: str, state: str) -> None:
    lab.sh(node, f"ip link set {iface} {state}")


def test_fo01_core_link_failure(lab_mod):
    """FO-01: cae PE1<->P1; el trafico CUST-A converge por P2 sin intervencion."""
    assert wait_until(lambda: lab.ping("h-a10", "10.10.30.10"), timeout=90)
    try:
        set_link("pe1", "eth1", "down")
        start = time.time()
        assert wait_until(lambda: lab.ping("h-a10", "10.10.30.10", count=1), timeout=60, interval=1)
        print(f"Reconvergencia en ~{time.time() - start:.1f} s")
        assert lab.isis_adjacencies_up("pe1") == 1
    finally:
        set_link("pe1", "eth1", "up")
    assert wait_until(lambda: lab.isis_adjacencies_up("pe1") == 2, timeout=90)


def test_fo02_stp_failover(lab_mod):
    """FO-02: cae la troncal activa SW-A1<->SW-A2; STP habilita la bloqueada."""
    states = lab.stp_port_states("sw-a2", ["eth1", "eth2"])
    active = next(p for p, s in states.items() if s == "forwarding")
    peer = {"eth1": "eth3", "eth2": "eth4"}[active]  # puerto equivalente en SW-A1
    try:
        set_link("sw-a1", peer, "down")
        assert wait_until(lambda: lab.ping("h-a20", "10.10.10.10", count=1), timeout=75, interval=2)
    finally:
        set_link("sw-a1", peer, "up")
