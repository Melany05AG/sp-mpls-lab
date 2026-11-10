#!/bin/sh
# Preparacion del kernel dentro del contenedor. La ejecuta containerlab (exec).
set -e
sysctl -qw net.ipv4.ip_forward=1
sysctl -qw net.ipv6.conf.all.disable_ipv6=0
sysctl -qw net.ipv6.conf.default.disable_ipv6=0
sysctl -qw net.ipv6.conf.all.forwarding=1
sysctl -qw net.ipv4.conf.all.rp_filter=0
sysctl -qw net.ipv4.conf.default.rp_filter=0

# Router-on-a-stick: troncal 802.1Q hacia SW-A1
ip link set eth2 up
ip link add link eth2 name eth2.10 type vlan id 10 2>/dev/null || true
ip link add link eth2 name eth2.20 type vlan id 20 2>/dev/null || true
ip addr replace 10.10.10.1/24 dev eth2.10
ip addr replace 10.10.20.1/24 dev eth2.20
ip link set eth2.10 up
ip link set eth2.20 up

# Reaplicar la configuracion de FRR ahora que existen VRF/subinterfaces
sleep 2
vtysh -b >/dev/null 2>&1 || true
echo "setup $(hostname) OK"
