#!/bin/sh
# Preparacion del kernel dentro del contenedor. La ejecuta containerlab (exec).
set -e
sysctl -qw net.ipv4.ip_forward=1
sysctl -qw net.ipv6.conf.all.disable_ipv6=0
sysctl -qw net.ipv6.conf.default.disable_ipv6=0
sysctl -qw net.ipv6.conf.all.forwarding=1
sysctl -qw net.ipv4.conf.all.rp_filter=0
sysctl -qw net.ipv4.conf.default.rp_filter=0

# NAT44 (PAT): LAN privada 192.168.50.0/24 -> 198.51.100.1 hacia la WAN
command -v iptables >/dev/null 2>&1 || apk add --no-cache iptables >/dev/null
iptables -t nat -C POSTROUTING -s 192.168.50.0/24 -o eth1 -j SNAT --to-source 198.51.100.1 2>/dev/null \
  || iptables -t nat -A POSTROUTING -s 192.168.50.0/24 -o eth1 -j SNAT --to-source 198.51.100.1

# Reaplicar la configuracion de FRR ahora que existen VRF/subinterfaces
sleep 2
vtysh -b >/dev/null 2>&1 || true
echo "setup $(hostname) OK"
