#!/usr/bin/env python3
"""Revision rapida del estado del plano de control (primer paso ante un incidente).

Uso: python3 automation/health_check.py
Codigo de salida 0 si todo coincide con el estado esperado, 1 si hay desviaciones.
"""
from __future__ import annotations

import sys

import lab

rows: list[tuple[str, str, str, str, bool]] = []


def check(node: str, item: str, expected: int, fn) -> None:
    try:
        actual = fn()
        rows.append((node, item, str(expected), str(actual), actual == expected))
    except Exception as exc:  # nodo caido o comando fallido
        rows.append((node, item, str(expected), f"ERROR: {exc}", False))


def main() -> int:
    for node, exp in lab.EXPECTED_ISIS.items():
        check(node, "IS-IS adyacencias Up", exp, lambda n=node: lab.isis_adjacencies_up(n))
    for node, exp in lab.EXPECTED_LDP.items():
        check(node, "LDP sesiones OPERATIONAL", exp, lambda n=node: lab.ldp_sessions_operational(n))
    check("pe1", "OSPF vrf CUST-A Full", 1, lambda: lab.ospf_full("pe1", "CUST-A"))
    check("pe3", "OSPF vrf CUST-A Full", 1, lambda: lab.ospf_full("pe3", "CUST-A"))
    for node, exp in lab.EXPECTED_OSPF.items():
        check(node, "OSPF vecinos Full", exp, lambda n=node: lab.ospf_full(n))
    for node, checks in lab.EXPECTED_BGP.items():
        for cmd, exp in checks:
            label = "BGP " + cmd.replace("show bgp ", "").replace(" summary json", "")
            check(node, label, exp, lambda n=node, c=cmd: lab.bgp_established(n, c))

    width = max(len(r[1]) for r in rows)
    print(f"{'NODO':<7} {'VERIFICACION':<{width}}  ESPERADO  ACTUAL")
    for node, item, exp, act, ok in rows:
        mark = "OK " if ok else "XX "
        print(f"{node:<7} {item:<{width}}  {exp:<8}  {mark}{act}")
    failed = [r for r in rows if not r[4]]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} verificaciones correctas")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
