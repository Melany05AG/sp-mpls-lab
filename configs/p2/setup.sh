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
for i in eth1 eth2 eth3 eth4; do sysctl -qw net.mpls.conf.$i.input=1; done

# Reaplicar la configuracion de FRR ahora que existen VRF/subinterfaces
sleep 2
vtysh -b >/dev/null 2>&1 || true
echo "setup $(hostname) OK"
