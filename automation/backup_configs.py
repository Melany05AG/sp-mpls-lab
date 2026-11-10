#!/usr/bin/env python3
"""Respaldo de configuraciones y evidencia de cambios.

Guarda `show running-config` de cada nodo FRR en backups/<marca de tiempo>/ y
genera CAMBIOS.diff comparando con el respaldo anterior. Se ejecuta antes y
despues de cada cambio; el diff se adjunta al registro de cambios.

Uso: python3 automation/backup_configs.py [--ticket CHG-0003]
"""
from __future__ import annotations

import argparse
import difflib
import sys
from datetime import datetime
from pathlib import Path

import lab

BACKUP_ROOT = Path(__file__).resolve().parent.parent / "backups"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket", default="", help="identificador del cambio, p. ej. CHG-0003")
    args = parser.parse_args()

    previous = sorted(p for p in BACKUP_ROOT.glob("*") if p.is_dir()) if BACKUP_ROOT.exists() else []
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + (f"_{args.ticket}" if args.ticket else "")
    target = BACKUP_ROOT / stamp
    target.mkdir(parents=True)

    errors = 0
    for node in lab.FRR_NODES:
        try:
            config = lab.vtysh(node, "show running-config")
            (target / f"{node}.conf").write_text(config)
        except Exception as exc:
            errors += 1
            print(f"[ERROR] {node}: {exc}", file=sys.stderr)
    print(f"Respaldo guardado en {target}")

    if previous:
        last = previous[-1]
        diff_lines: list[str] = []
        for conf in sorted(target.glob("*.conf")):
            old = last / conf.name
            old_text = old.read_text().splitlines(keepends=True) if old.exists() else []
            diff_lines += difflib.unified_diff(old_text, conf.read_text().splitlines(keepends=True),
                                               fromfile=f"{last.name}/{conf.name}",
                                               tofile=f"{target.name}/{conf.name}")
        (target / "CAMBIOS.diff").write_text("".join(diff_lines))
        changed = sum(1 for line in diff_lines if line.startswith("+++"))
        print(f"Comparado con {last.name}: {changed} archivo(s) con cambios -> CAMBIOS.diff")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
