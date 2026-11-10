"""Utilidades comunes para operar el laboratorio SP-Lab.

Ejecuta comandos dentro de los contenedores de containerlab con `docker exec`,
sin dependencias externas. Los nombres siguen la convencion de containerlab:
clab-<nombre-del-lab>-<nodo>.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any

LAB_NAME = os.environ.get("SPLAB_NAME", "sp-lab")
DOCKER = os.environ.get("SPLAB_DOCKER", "docker").split()

CORE = ["p1", "p2"]
PE = ["pe1", "pe2", "pe3"]
CE = ["ce-a1", "ce-a2", "ce-b1", "ce-b2"]
SWITCHES = ["sw-a1", "sw-a2"]
FRR_NODES = CORE + PE + CE + SWITCHES
ROUTERS = CORE + PE + CE  # nodos con plano de control FRR activo

# Estado esperado (fuente de verdad para validaciones y health check)
EXPECTED_ISIS = {"p1": 4, "p2": 4, "pe1": 2, "pe2": 2, "pe3": 2}
EXPECTED_LDP = {"p1": 4, "p2": 4, "pe1": 2, "pe2": 2, "pe3": 2}
EXPECTED_BGP = {
    # nodo: [(comando de resumen, numero de sesiones Established esperadas)]
    "p1": [("show bgp ipv4 vpn summary json", 3), ("show bgp ipv6 vpn summary json", 3),
           ("show bgp l2vpn evpn summary json", 3)],
    "pe1": [("show bgp ipv4 vpn summary json", 1), ("show bgp vrf CUST-B ipv4 unicast summary json", 1),
            ("show bgp vrf CUST-B ipv6 unicast summary json", 1)],
    "pe2": [("show bgp ipv4 vpn summary json", 1), ("show bgp l2vpn evpn summary json", 1),
            ("show bgp vrf CUST-B ipv4 unicast summary json", 1),
            ("show bgp vrf CUST-B ipv6 unicast summary json", 1)],
    "pe3": [("show bgp ipv4 vpn summary json", 1), ("show bgp l2vpn evpn summary json", 1)],
    "ce-b1": [("show bgp ipv4 unicast summary json", 1), ("show bgp ipv6 unicast summary json", 1)],
    "ce-b2": [("show bgp ipv4 unicast summary json", 1), ("show bgp ipv6 unicast summary json", 1)],
}
EXPECTED_OSPF = {"ce-a1": 1, "ce-a2": 1}


def container(node: str) -> str:
    return f"clab-{LAB_NAME}-{node}"


def run(node: str, cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(DOCKER + ["exec", container(node)] + cmd,
                          capture_output=True, text=True, timeout=timeout)


def sh(node: str, command: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Ejecuta un comando de shell en el nodo."""
    return run(node, ["sh", "-c", command], timeout=timeout)


def vtysh(node: str, command: str) -> str:
    """Ejecuta un comando de FRR (vtysh) y devuelve la salida en texto."""
    res = run(node, ["vtysh", "-c", command])
    if res.returncode != 0:
        raise RuntimeError(f"{node}: '{command}' fallo: {res.stderr.strip()}")
    return res.stdout


def vtysh_json(node: str, command: str) -> Any:
    out = vtysh(node, command)
    return json.loads(out) if out.strip() else {}


def ping(node: str, target: str, count: int = 3, v6: bool = False) -> bool:
    cmd = ["ping", "-6" if v6 else "-4", "-c", str(count), "-W", "1", target]
    return run(node, cmd, timeout=count * 3 + 5).returncode == 0


# ---------------------------------------------------------------- parsers

def isis_adjacencies_up(node: str) -> int:
    """Cuenta adyacencias IS-IS en estado Up (salida en texto, estable entre versiones)."""
    out = vtysh(node, "show isis neighbor")
    return sum(1 for line in out.splitlines() if re.search(r"\sUp\s", line))


def ldp_sessions_operational(node: str) -> int:
    out = vtysh(node, "show mpls ldp neighbor")
    return sum(1 for line in out.splitlines() if "OPERATIONAL" in line)


def ospf_full(node: str, vrf: str | None = None) -> int:
    cmd = f"show ip ospf vrf {vrf} neighbor" if vrf else "show ip ospf neighbor"
    out = vtysh(node, cmd)
    return sum(1 for line in out.splitlines() if "Full/" in line)


def _find_peers(data: Any) -> dict:
    """Busca el diccionario 'peers' en la salida JSON de un 'summary' de BGP."""
    if isinstance(data, dict):
        if isinstance(data.get("peers"), dict):
            return data["peers"]
        for value in data.values():
            found = _find_peers(value)
            if found:
                return found
    return {}


def bgp_peers(node: str, command: str) -> dict[str, str]:
    """Devuelve {vecino: estado} para un comando 'show bgp ... summary json'."""
    peers = _find_peers(vtysh_json(node, command))
    return {peer: info.get("state", "?") for peer, info in peers.items()}


def bgp_established(node: str, command: str) -> int:
    return sum(1 for s in bgp_peers(node, command).values() if s == "Established")


def stp_port_states(node: str, ports: list[str]) -> dict[str, str]:
    """Estado STP de cada puerto del puente Linux (forwarding, blocking, ...)."""
    out = sh(node, "bridge link show").stdout
    states = {}
    for port in ports:
        match = re.search(rf"\b{port}@?\S*:.*?state (\w+)", out)
        states[port] = match.group(1) if match else "unknown"
    return states
