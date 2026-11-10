#!/bin/sh
# SW-A1: puente raiz de STP (prioridad 4096). Troncales: eth1 (CE-A1), eth3/eth4 (SW-A2). Acceso VLAN 10: eth2.
set -e
ip link add br0 type bridge vlan_filtering 1 stp_state 1 priority 4096 2>/dev/null || true
ip link set br0 up
for p in eth1 eth3 eth4; do
  ip link set $p master br0; ip link set $p up
  bridge vlan add dev $p vid 10
  bridge vlan add dev $p vid 20
done
ip link set eth2 master br0; ip link set eth2 up
bridge vlan add dev eth2 vid 10 pvid untagged
bridge vlan del dev eth2 vid 1
echo "setup $(hostname) OK"
