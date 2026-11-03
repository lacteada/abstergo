# Resumen del código — abstergo

Revisión de tamaño, estructura y código innecesario.

- Fecha: 2026-11-02
- Recon (regenerable): `cd ~/code/ina/backend/abstergo && for d in apps/*/ config/; do find "$d" -name '*.py' -not -path '*/migrations/*' | xargs wc -l | tail -1; done`, más `ruff check .` y `vulture apps config --min-confidence 80`.

## 1. Tamaño

- **~7.400 líneas** de Python (sin `venv`), en **92 archivos** (sin migraciones) y **31 migraciones**.
- 46 plantillas HTML, 6 archivos JS, 3 CSS.

Por app (Python, sin migraciones):

| App | Líneas | Archivos | Rol |
|---|---|---|---|
| cuentas | 1.647 | 13 | Usuario, Rol, autenticación, OTP, invitaciones |
| common | 1.278 | 16 | Base compartida: vistas, formularios, permisos, delegaciones |
| api | 632 | 5 | API v1 (DRF) para el cliente móvil |
| catalogos | 523 | 8 | Meta, TipoAtencion, SubAtencion |
| atenciones | 483 | 8 | Transacción de atención |
| organizacion | 386 | 8 | Delegacion, Cargo |
| ciudadanos | 365 | 11 | Vecino (incluye comando de relleno) |
| panel | 353 | 9 | Dashboard y comando `cargar_datos` |
| cumplimiento | 324 | 5 | Ley 21.719: auditoría y modelos |
| config | 280 | 5 | Settings, urls, wsgi |

## 2. Estructura

- 9 apps propias; dominio en español y contrato de API en inglés.
- Lógica transversal en `apps/common/` (una sola fuente por regla).
- CRUD declarativo: cada mantenedor solo declara modelo, formulario, título y rutas; el comportamiento vive en `vistas_base.py`.

## 3. Código innecesario

- **`ruff check .` → limpio** (incluye imports y variables sin usar).
- **`vulture` al 80%**: sin hallazgos reales; solo falsos positivos de framework (parámetros `sender` de señales y fixtures `db`).
- **Plantillas y JS huérfanos**: ninguno (toda plantilla y script está referenciado).

Conclusión: **no hay código muerto relevante**. Lo que podría parecer de más se conserva a propósito:

- **Django Admin** (13 registros): respaldo técnico y administración de las tablas de la Ley 21.719; no se usa para las operaciones del sistema.
- **`apps/cumplimiento/models.py`**: modelos de la ley, hoy parciales; `cumplimiento/auditoria.py` **sí** se usa (lo llaman `common` y `atenciones`).
- **`apps/api/`**: aunque la web no lo use, lo consume el cliente Android.

Recomendación: no eliminar código; el proyecto ya está ajustado. Si se quiere reducir superficie, el único candidato real es retirar los registros de `admin.py`, y no conviene (rompe la gestión de las tablas de la ley).
