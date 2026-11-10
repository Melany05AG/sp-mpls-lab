#!/bin/sh
# SW-A2: prioridad STP por defecto (32768). Troncales redundantes eth1/eth2 hacia SW-A1:
# STP debe bloquear una de las dos. Acceso VLAN 20: eth3.
set -e
ip link add br0 type bridge vlan_filtering 1 stp_state 1 priority 32768 2>/dev/null || true
ip link set br0 up
for p in eth1 eth2; do
  ip link set $p master br0; ip link set $p up
  bridge vlan add dev $p vid 10
  bridge vlan add dev $p vid 20
done
ip link set eth3 master br0; ip link set eth3 up
bridge vlan add dev eth3 vid 20 pvid untagged
bridge vlan del dev eth3 vid 1
echo "setup $(hostname) OK"
