#!/bin/sh
# Simula la caida o recuperacion de un enlace para practicar el runbook.
# Uso: ./scripts/simulate-failure.sh <nodo> <interfaz> <down|up>
# Ejemplo: ./scripts/simulate-failure.sh pe1 eth1 down
set -e
if [ $# -ne 3 ]; then
  echo "Uso: $0 <nodo> <interfaz> <down|up>" >&2
  exit 1
fi
node=$1; iface=$2; state=$3
case "$state" in down|up) ;; *) echo "estado invalido: $state" >&2; exit 1 ;; esac
docker exec "clab-sp-lab-$node" ip link set "$iface" "$state"
echo "$(date '+%Y-%m-%d %H:%M:%S') $node $iface -> $state"
