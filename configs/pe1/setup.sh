#!/bin/sh
# Preparacion del kernel dentro del contenedor. La ejecuta containerlab (exec).
set -e
sysctl -qw net.ipv4.ip_forward=1
sysctl -qw net.ipv6.conf.all.disable_ipv6=0
sysctl -qw net.ipv6.conf.default.disable_ipv6=0
sysctl -qw net.ipv6.conf.all.forwarding=1
sysctl -qw net.ipv4.conf.all.rp_filter=0
sysctl -qw net.ipv4.conf.default.rp_filter=0

# MPLS: tabla de etiquetas y entrada MPLS en enlaces del nucleo
sysctl -qw net.mpls.platform_labels=1048575
for i in eth1 eth2; do sysctl -qw net.mpls.conf.$i.input=1; done

# Sesiones BGP/OSPF dentro de VRF
sysctl -qw net.ipv4.tcp_l3mdev_accept=1
sysctl -qw net.ipv4.udp_l3mdev_accept=1

# VRF CUST-A (tabla 10) en eth3
ip link add CUST-A type vrf table 10 2>/dev/null || true
ip link set CUST-A up
ip link set eth3 master CUST-A
ip link set eth3 up
ip addr replace 172.16.1.1/30 dev eth3

# VRF CUST-B (tabla 20) en eth4
ip link add CUST-B type vrf table 20 2>/dev/null || true
ip link set CUST-B up
ip link set eth4 master CUST-B
ip link set eth4 up
ip addr replace 172.16.2.1/30 dev eth4
ip -6 addr replace 2001:db8:100:1::1/64 dev eth4

# Reaplicar la configuracion de FRR ahora que existen VRF/subinterfaces
sleep 2
vtysh -b >/dev/null 2>&1 || true
echo "setup $(hostname) OK"
