# 02 · Procedimiento de implementación (MOP)

Procedimiento paso a paso para desplegar el laboratorio y, como ejemplo, para aplicar un cambio sobre la red en operación. Cada paso tiene su verificación y su reversión.

## A. Despliegue inicial

### Requisitos

| Requisito | Detalle |
|---|---|
| Sistema | Linux (Ubuntu 22.04/24.04) o WSL2 con kernel que tenga MPLS (`/proc/sys/net/mpls`) |
| Software | Docker, [containerlab](https://containerlab.dev/install/), Python 3.10+, `make` |
| Recursos | 4 vCPU y 4 GB de RAM son suficientes (18 contenedores ligeros) |
| Usuario | En el grupo `docker` para que los scripts ejecuten `docker exec` sin sudo |

### Pasos

| # | Acción | Comando | Verificación |
|---|---|---|---|
| 1 | Cargar módulos del kernel | `make prep` | Todos los módulos `OK`, existe `/proc/sys/net/mpls` |
| 2 | Desplegar topología | `make deploy` | 18 nodos en `running` (`make inspect`) y `setup <nodo> OK` en la salida |
| 3 | Esperar convergencia | ~60 s | STP necesita 30 s (2 × forward delay) |
| 4 | Revisar plano de control | `make check` | Todas las verificaciones en `OK` |
| 5 | Pruebas de servicio | `make test` | Todas las pruebas pasan |
| 6 | Respaldo de línea base | `make backup TICKET=CHG-0001` | Carpeta nueva en `backups/` |
| 7 | Registrar | `docs/04-registro-cambios.md` | Entrada con resultado y evidencia |

### Reversión

`make destroy` elimina todos los contenedores y enlaces; el host queda como antes del paso 2.

## B. Ejemplo de cambio: agregar un sitio a CUST-A

Este es el formato a seguir para cualquier cambio sobre la red en operación.

**Cambio:** CHG-0002 · Nuevo prefijo 10.10.40.0/24 en CUST-A sitio 2 (CE-A2).
**Impacto esperado:** ninguno sobre el servicio existente. **Ventana:** cualquiera (laboratorio).

| # | Acción | Comando | Verificación |
|---|---|---|---|
| 1 | Respaldo previo | `make backup TICKET=CHG-0002-pre` | Respaldo creado |
| 2 | Estado previo | `make check && make test` | Todo en verde (si no, se detiene el cambio) |
| 3 | Crear interfaz | `docker exec clab-sp-lab-ce-a2 ip link add lan40 type dummy && docker exec clab-sp-lab-ce-a2 ip link set lan40 up` | `ip link show lan40` en UP |
| 4 | Configurar | `docker exec -it clab-sp-lab-ce-a2 vtysh` → `conf t` / `interface lan40` / `ip address 10.10.40.1/24` / `router ospf` / `network 10.10.40.0/24 area 0` / `end` / `write` | `show ip ospf interface lan40` |
| 5 | Verificar propagación | `docker exec clab-sp-lab-pe1 vtysh -c "show ip route vrf CUST-A 10.10.40.0/24"` | Ruta presente con etiqueta VPN |
| 6 | Verificar servicio | `docker exec clab-sp-lab-h-a10 ping -c 3 10.10.40.1` | 0 % de pérdida |
| 7 | Regresión | `make test` | Todas las pruebas pasan |
| 8 | Respaldo posterior y evidencia | `make backup TICKET=CHG-0002` | `CAMBIOS.diff` muestra solo las líneas de CE-A2 |
| 9 | Registrar | `docs/04-registro-cambios.md` | Entrada completa |

**Reversión:** en CE-A2, `no network 10.10.40.0/24 area 0`, `no interface lan40`, `write`; `ip link del lan40`; repetir `make test`.
