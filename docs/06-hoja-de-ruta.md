# 06 · Hoja de ruta

Fases siguientes, en orden de valor para una red de proveedor.

| Fase | Tema | Qué se agrega | Estado |
|---|---|---|---|
| 2 | Segment Routing (SR-MPLS) | Reemplazar LDP por SIDs de IS-IS; comparar tablas MPLS antes y después | Pendiente |
| 3 | BFD | Detección de fallas en milisegundos para IS-IS y BGP; medir la mejora con FO-01 | Pendiente |
| 4 | Segundo route reflector | Eliminar el punto único de falla del plano de control | Pendiente |
| 5 | OSPFv3 / IPv6 en CUST-A | Doble pila también en el cliente con OSPF | Pendiente |
| 6 | CGNAT | NAT444 en el borde del proveedor con el rango 100.64.0.0/10 | Pendiente |
| 7 | RSTP/MSTP | `mstpd` en los switches de acceso | Pendiente |
| 8 | SRv6 y RSVP-TE | Requiere imágenes de fabricante (Cisco XRd, Juniper vJunos-router) | Pendiente |
| 9 | Plantillas | Generar las configuraciones desde un inventario YAML con Jinja2 | Pendiente |

## Fase 2: referencia de SR-MPLS en FRR

```
router isis CORE
 segment-routing on
 segment-routing global-block 16000 23999
 segment-routing node-msd 8
 segment-routing prefix 10.255.0.11/32 index 11
exit
```

Con un índice por nodo igual al último octeto de la loopback, la etiqueta de cada PE es predecible (16000 + índice: PE1 = 16011). Después se retira `mpls ldp` y se valida que CP-04 y SV-01 sigan pasando.
