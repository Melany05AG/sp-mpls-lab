#!/bin/sh
# Carga los modulos del kernel que necesitan MPLS, VRF y VXLAN.
# Los contenedores comparten el kernel del host, asi que esto se hace una vez en el host.
set -e
for m in mpls_router mpls_iptunnel mpls_gso vrf vxlan bridge 8021q; do
  if modprobe "$m" 2>/dev/null; then
    echo "modulo $m: OK"
  else
    echo "modulo $m: no disponible (revisa el kernel del host / WSL)" >&2
  fi
done
if [ ! -d /proc/sys/net/mpls ]; then
  echo "ERROR: el kernel no tiene MPLS habilitado; L3VPN no funcionara." >&2
  exit 1
fi
