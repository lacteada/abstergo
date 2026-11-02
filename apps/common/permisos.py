"""Autorización por rol y cargo, en un solo lugar.

La matriz dice, por módulo, qué roles y qué cargos pueden **leer** y qué roles
y cargos pueden **escribir**. La web y la API la consultan por igual; ninguna
vista ramifica por rol o cargo por su cuenta. Para cambiarla, se edita acá y
listo. El permiso se resuelve por unión: pasa quien concede por `rol` **o** por
`cargo`.

Las claves de módulo viajan en el contrato (``/auth/me/`` devuelve
``read_modules`` y ``write_modules``), así que están en inglés, igual que el
resto del contrato público.
"""

ADMIN = "admin"
COORDINADOR = "coordinador"
DELEGADO = "delegado"
FUNCIONARIO = "funcionario"
VERIFICADOR = "verificador"
CONSULTA = "consulta"

# Códigos de `Rol.codigo` que existen en el sistema.
ROLES = [ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR, CONSULTA]

# Códigos de `Cargo.codigo`: el puesto funcional dentro de la delegación. No
# son roles de acceso; conviven con ellos (un usuario tiene rol y cargo). Salen
# del descriptor de funciones de las Delegaciones y se siembran desde
# `datos_nuevos/cargos.json`.
CARGO_DELEGADO = "delegado"
CARGO_GESTOR_SOCIAL = "gestor-social"
CARGO_APOYO_ADMINISTRATIVO = "apoyo-administrativo"
CARGO_ORGANIZACIONES_COMUNITARIAS = "organizaciones-comunitarias"
CARGO_GESTOR_COMPRAS = "gestor-de-compras-y-proyectos"
CARGO_GESTION_PLANIFICACION = "gestion-y-planificacion"
CARGO_COORDINADOR_SERVICIOS = "coordinador-de-servicios-comunitarios"

CARGOS = [
    CARGO_DELEGADO,
    CARGO_GESTOR_SOCIAL,
    CARGO_APOYO_ADMINISTRATIVO,
    CARGO_ORGANIZACIONES_COMUNITARIAS,
    CARGO_GESTOR_COMPRAS,
    CARGO_GESTION_PLANIFICACION,
    CARGO_COORDINADOR_SERVICIOS,
]

# Los que ven por encima de las delegaciones: no se acotan a un territorio.
ALCANCE_GLOBAL = {ADMIN}

# Matriz de permisos por módulo:
# - admin: acceso total (delegaciones, roles, usuarios globales, catálogos, atenciones, vecinos).
# - delegado: gestiona usuarios en su delegación, consulta vecinos y atenciones.
# - funcionario: consulta vecinos con su historial y crea/gestiona atenciones.
# - coordinador, verificador, consulta: sin permisos operativos por ahora (inútiles/deshabilitados).
MATRIZ = {
    "cases": {
        "read": {ADMIN, DELEGADO, FUNCIONARIO},
        "write": {ADMIN, DELEGADO, FUNCIONARIO},
    },
    "neighbors": {
        "read": {ADMIN, DELEGADO, FUNCIONARIO},
        "write": {ADMIN, FUNCIONARIO},
    },
    "delegations": {
        "read": {ADMIN},
        "write": {ADMIN},
    },
    "goals": {
        "read": {ADMIN},
        "write": {ADMIN},
    },
    "attention_types": {
        "read": {ADMIN, DELEGADO, FUNCIONARIO},
        "write": {ADMIN},
    },
    "attention_subtypes": {
        "read": {ADMIN, DELEGADO, FUNCIONARIO},
        "write": {ADMIN},
    },
    "users": {
        "read": {ADMIN, DELEGADO},
        "write": {ADMIN, DELEGADO},
    },
    "roles": {
        "read": {ADMIN},
        "write": {ADMIN},
    },
    "positions": {
        "read": {ADMIN},
        "write": {ADMIN},
    },
}

# Matriz de permisos por cargo, con la misma forma que `MATRIZ`: por módulo,
# qué cargos leen y qué cargos escriben. Suma a lo que concede el rol. Refleja
# el "Descriptor de funciones para los cargos de las Delegaciones" (2026); si
# se ajusta, es solo acá.
MATRIZ_CARGO = {
    "cases": {
        "read": set(CARGOS),
        "write": {
            CARGO_DELEGADO,
            CARGO_GESTOR_SOCIAL,
            CARGO_APOYO_ADMINISTRATIVO,
            CARGO_COORDINADOR_SERVICIOS,
        },
    },
    "neighbors": {
        "read": set(CARGOS),
        "write": {CARGO_GESTOR_SOCIAL, CARGO_ORGANIZACIONES_COMUNITARIAS},
    },
    "goals": {
        "read": {CARGO_GESTOR_COMPRAS, CARGO_GESTION_PLANIFICACION},
        "write": {CARGO_GESTION_PLANIFICACION},
    },
    "attention_types": {
        "read": {CARGO_DELEGADO, CARGO_GESTOR_SOCIAL},
        "write": set(),
    },
    "attention_subtypes": {
        "read": {CARGO_DELEGADO, CARGO_GESTOR_SOCIAL},
        "write": set(),
    },
}

# Modelo -> módulo. Las vistas web no repiten la asignación: la derivan del
# modelo que ya declaran.
MODELO_A_MODULO = {
    "Atencion": "cases",
    "Vecino": "neighbors",
    "Delegacion": "delegations",
    "Cargo": "positions",
    "Meta": "goals",
    "TipoAtencion": "attention_types",
    "SubAtencion": "attention_subtypes",
    "Usuario": "users",
    "Rol": "roles",
}


def codigo_de(usuario):
    """El código de rol del usuario. El superusuario cuenta como `admin`."""
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return None
    if usuario.is_superuser:
        return ADMIN
    return usuario.rol.codigo if usuario.rol_id else None


def cargo_de(usuario):
    """El código de cargo del usuario, o None si no tiene."""
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return None
    return usuario.cargo.codigo if getattr(usuario, "cargo_id", None) else None


def puede(usuario, modulo, escritura=False):
    """¿El usuario puede leer (o escribir) ese módulo?

    Concede el rol **o** el cargo. Así un cargo de la delegación amplía lo que
    ya permite el rol, sin ramificar por rol en ningún otro lugar.
    """
    clave = "write" if escritura else "read"
    if codigo_de(usuario) in MATRIZ.get(modulo, {}).get(clave, set()):
        return True
    return cargo_de(usuario) in MATRIZ_CARGO.get(modulo, {}).get(clave, set())


def modulo_de(modelo):
    """El módulo de un modelo, o None si no está mapeado."""
    return MODELO_A_MODULO.get(modelo.__name__) if modelo else None


def alcance_global(usuario):
    """¿El rol del usuario ve por encima de las delegaciones?

    Admin y coordinador no se acotan a un territorio: ven todos los registros.
    El resto trabaja solo con las delegaciones que tiene autorizadas.
    """
    return codigo_de(usuario) in ALCANCE_GLOBAL


def modulos_de(usuario, escritura=False):
    """Los módulos que el usuario puede leer (o escribir), por rol y por cargo."""
    clave = "write" if escritura else "read"
    modulos = set()
    codigo = codigo_de(usuario)
    if codigo:
        modulos |= {m for m, p in MATRIZ.items() if codigo in p[clave]}
    cargo = cargo_de(usuario)
    if cargo:
        modulos |= {m for m, p in MATRIZ_CARGO.items() if cargo in p[clave]}
    return modulos
