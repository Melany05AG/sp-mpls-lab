# 04 · Registro de cambios

Cada cambio en la infraestructura queda registrado aquí con su evidencia. La evidencia es el `CAMBIOS.diff` generado por `make backup TICKET=<id>` y la salida de `make test`.

| ID | Fecha | Tipo | Descripción | Nodos | Resultado | Evidencia |
|---|---|---|---|---|---|---|
| CHG-0001 | _(fecha del despliegue)_ | Implementación | Línea base: núcleo IS-IS/MPLS, RR, L3VPN CUST-A y CUST-B, EVPN CUST-C | Todos | _(Exitoso / Revertido)_ | `backups/<fecha>_CHG-0001/` |

Tipos: Implementación · Ampliación · Corrección · Nueva tecnología · Reversión.

## Plantilla de solicitud de cambio

```
ID: CHG-NNNN
Solicitante:                     Fecha:
Tipo:
Descripción y justificación:
Nodos afectados:
Impacto esperado en clientes:
Riesgo (bajo / medio / alto) y mitigación:
Procedimiento: (enlace a la sección del MOP)
Plan de reversión:
Verificación posterior:
Resultado:
Evidencia: backups/<carpeta>/CAMBIOS.diff, salida de make test
```
