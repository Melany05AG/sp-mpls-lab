# 05 · Plan de pruebas

Todas las pruebas están automatizadas con pytest (`make test`; las de falla con `make failover`). Los identificadores coinciden con los nombres de las funciones de prueba.

## Plano de control (`tests/test_control_plane.py`)

| ID | Qué valida | Resultado esperado |
|---|---|---|
| CP-01 | Adyacencias IS-IS | P1/P2: 4 en Up; cada PE: 2 en Up |
| CP-02 | Loopbacks en el IGP | Todas las loopbacks IPv4 e IPv6 aprendidas por IS-IS |
| CP-03 | Sesiones LDP | P1/P2: 4; cada PE: 2 en OPERATIONAL |
| CP-04 | LSP de PE1 a PE remotos | Etiqueta asignada y en uso hacia 10.255.0.12 y .13 |
| CP-05 | Sesiones BGP | iBGP al RR (VPNv4, VPNv6, EVPN) y eBGP PE-CE (v4/v6) en Established |
| CP-06 | Núcleo libre de BGP | P2 sin `router bgp` |
| CP-07 | OSPF PE-CE | Vecino Full en la VRF CUST-A de PE1 y PE3 |
| CP-08 | Ruta VPN etiquetada | 10.10.30.0/24 en VRF CUST-A de PE1 con etiqueta |
| CP-09 | Filtro de anuncios | 192.168.50.0/24 ausente y 198.51.100.1/32 presente en la VRF CUST-B |

## Servicios (`tests/test_services.py`)

| ID | Qué valida | Resultado esperado |
|---|---|---|
| SV-01 | L3VPN CUST-A entre sitios | Ping exitoso desde VLAN 10 y 20 al sitio 2, y de vuelta |
| SV-02 | Enrutamiento entre VLAN | H-A10 alcanza H-A20 a través de CE-A1 |
| SV-03 | STP | En SW-A2 una troncal en forwarding y la otra en blocking |
| SV-04 | Puente raíz | SW-A1 es la raíz |
| SV-05 | NAT | H-B1 alcanza H-B2 y el contador SNAT de CE-B1 aumenta |
| SV-06 | Direcciones privadas | H-B2 no alcanza 192.168.50.10 |
| SV-07 | IPv6 / 6VPE | H-B1 alcanza 2001:db8:b2::10 |
| SV-08 | Aislamiento entre VRF | CUST-A y CUST-B no se alcanzan entre sí |
| SV-09 | Descubrimiento EVPN | PE2 lista a PE3 (10.255.0.13) como VTEP remoto del VNI 30030 |
| SV-10 | L2VPN | H-C1 alcanza H-C2 y PE2 aprende MAC remotas por EVPN |

## Resiliencia (`tests/test_failover.py`, `make failover`)

| ID | Falla provocada | Resultado esperado |
|---|---|---|
| FO-01 | Cae PE1–P1 | CUST-A se recupera por P2 sin intervención; se reporta el tiempo de reconvergencia |
| FO-02 | Cae la troncal activa SW-A1–SW-A2 | STP habilita la troncal bloqueada y H-A20 recupera conectividad |

## Registro de ejecución

| Fecha | Commit | Resultado | Observaciones |
|---|---|---|---|
| _(completar)_ | | _(n pruebas, n fallidas)_ | |
