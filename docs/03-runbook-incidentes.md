# 03 · Runbook de incidentes

Guía para diagnosticar, escalar y resolver incidentes. El orden de revisión va **de abajo hacia arriba**: enlace → IGP → MPLS → BGP → servicio.

## Flujo general

1. **Registrar** hora de inicio, síntoma reportado y clientes afectados.
2. **Delimitar** con `make check`: muestra qué nodo y qué capa se desvían del estado esperado.
3. **Diagnosticar** con el escenario correspondiente (abajo).
4. **Escalar** si no se resuelve en el tiempo objetivo o si afecta a varios clientes.
5. **Resolver y verificar** con `make test`.
6. **Documentar**: causa raíz, acciones y evidencia en el registro de cambios / incidentes.

### Severidad

| Severidad | Criterio | Objetivo de atención |
|---|---|---|
| S1 | Varios clientes sin servicio, o falla del núcleo sin redundancia | Inmediato, escalar de una vez |
| S2 | Un cliente sin servicio, o pérdida de redundancia del núcleo | 15 minutos |
| S3 | Degradación sin pérdida de servicio | 4 horas |

Acceso a un nodo: `docker exec -it clab-sp-lab-<nodo> vtysh`

---

## INC-01 · Adyacencia IS-IS caída

**Síntoma:** `make check` muestra menos adyacencias IS-IS en un nodo; posible pérdida de redundancia.

| Paso | Comando | Qué buscar |
|---|---|---|
| 1 | `show isis neighbor` | Qué vecino falta |
| 2 | `show interface ethX` (o `ip link show ethX`) | Interfaz `down` → problema físico/enlace |
| 3 | `show isis interface ethX detail` | Tipo de circuito (`level-2-only`, `point-to-point`) igual en ambos extremos |
| 4 | `ping 10.0.0.X` al otro extremo del /31 | Conectividad L3 del enlace |
| 5 | `show isis database` | LSP del vecino presentes |

**Causas típicas:** interfaz caída, discrepancia de tipo de red (p2p vs broadcast), nivel distinto, área distinta, MTU. **Práctica:** `./scripts/simulate-failure.sh pe1 eth1 down`.

## INC-02 · Sesión LDP caída o LSP faltante

**Síntoma:** IS-IS está bien, pero el tráfico VPN no pasa; `show ip route vrf X` muestra la ruta sin etiqueta de transporte.

| Paso | Comando | Qué buscar |
|---|---|---|
| 1 | `show mpls ldp neighbor` | Sesión `OPERATIONAL` con cada vecino |
| 2 | `show mpls ldp discovery` | Hellos enviados y recibidos en la interfaz |
| 3 | `show mpls ldp binding 10.255.0.X/32` | Etiqueta local y remota para la loopback del PE destino |
| 4 | `show mpls table` | Entradas en la LFIB |
| 5 | `sysctl net.mpls.conf.ethX.input` (shell) | Debe ser `1`; si es `0`, el kernel descarta los paquetes etiquetados |

**Causas típicas:** interfaz no habilitada en LDP, transport-address no alcanzable, `net.mpls.conf.*.input=0`, módulo `mpls_router` no cargado en el host.

## INC-03 · Sesión BGP VPN caída

**Síntoma:** un PE pierde todas las rutas VPN.

| Paso | Comando | Qué buscar |
|---|---|---|
| 1 | `show bgp ipv4 vpn summary` | Estado del vecino 10.255.0.1 (RR) |
| 2 | `ping 10.255.0.1 -I 10.255.0.11` (shell) | Alcanzabilidad entre loopbacks |
| 3 | `show bgp neighbor 10.255.0.1` | `update-source`, AS remoto, último error |
| 4 | `show bgp ipv4 vpn` | Rutas recibidas por RD |

**Causas típicas:** falta `update-source lo`, loopback no anunciada en IS-IS, AF no activada en uno de los extremos. Si el RR cae, **todos** los PE pierden rutas nuevas: es S1 (la mejora natural es un segundo RR, ver hoja de ruta).

## INC-04 · Cliente L3VPN sin conectividad entre sitios

| Paso | Dónde | Comando | Qué buscar |
|---|---|---|---|
| 1 | CE | `show ip route` | Ruta al sitio remoto |
| 2 | PE local | `show ip ospf vrf CUST-A neighbor` / `show bgp vrf CUST-B summary` | Protocolo PE-CE arriba |
| 3 | PE local | `show bgp vrf CUST-A ipv4 unicast` | Prefijo local importado a BGP |
| 4 | PE local | `show bgp ipv4 vpn` | Prefijo exportado con el RD y RT correctos |
| 5 | PE remoto | `show bgp ipv4 vpn rd 65000:101` | Prefijo recibido desde el RR |
| 6 | PE remoto | `show ip route vrf CUST-A <prefijo>` | Instalado con etiqueta VPN y next-hop resuelto |

**Causas típicas:** RT de importación distinto al de exportación, falta `redistribute` entre el protocolo PE-CE y BGP, prefix-list de entrada que descarta el prefijo, next-hop BGP sin LSP (ver INC-02).

## INC-05 · L2VPN EVPN sin conectividad

| Paso | Comando (PE2/PE3) | Qué buscar |
|---|---|---|
| 1 | `show evpn vni 30030` | VTEP remoto listado |
| 2 | `show bgp l2vpn evpn route type multicast` | Ruta tipo 3 del otro PE |
| 3 | `show evpn mac vni 30030` | MAC locales y remotas |
| 4 | `ip -d link show vxlan30030` (shell) | `local` = loopback, puerto 4789, `nolearning` |
| 5 | `bridge fdb show dev vxlan30030` (shell) | Entradas hacia el VTEP remoto |

**Causas típicas:** falta `advertise-all-vni`, AF `l2vpn evpn` sin activar en el RR, interfaz del cliente fuera del bridge.

## INC-06 · Lazo o cambio de topología STP

| Paso | Comando (shell en SW-A1/SW-A2) | Qué buscar |
|---|---|---|
| 1 | `bridge link show` | Estado de cada puerto (forwarding / blocking) |
| 2 | `cat /sys/class/net/br0/bridge/root_id` | Mismo puente raíz en ambos switches |
| 3 | `cat /sys/class/net/br0/bridge/topology_change` | Cambios de topología recientes |
| 4 | `bridge vlan show` | VLAN permitidas en cada troncal |

**Causas típicas:** STP deshabilitado (`stp_state 0`) con enlaces redundantes, prioridad mal configurada que cambia la raíz, VLAN faltante en una troncal.

## INC-07 · NAT no traduce

| Paso | Comando (shell en CE-B1) | Qué buscar |
|---|---|---|
| 1 | `iptables -t nat -L POSTROUTING -v -n` | Contador de la regla SNAT aumenta |
| 2 | `ip addr show lo` | 198.51.100.1/32 presente |
| 3 | `vtysh -c "show bgp ipv4 unicast neighbors 172.16.2.1 advertised-routes"` | Se anuncia 198.51.100.1/32 |
| 4 | `tcpdump -ni eth1 icmp` | Origen traducido a 198.51.100.1 |

## Plantilla de reporte de incidente

```
ID: INC-AAAAMMDD-NN          Severidad: S1 / S2 / S3
Inicio:                      Fin:                 Duración:
Síntoma reportado:
Clientes / servicios afectados:
Diagnóstico (comandos y hallazgos):
Causa raíz:
Acciones de resolución:
Escalado a / hora:
Verificación (make test):
Acciones preventivas:
```
