"""Autorización por rol, en un solo lugar.

La matriz dice, por módulo, qué roles pueden **leer** y qué roles pueden
**escribir**. La web y la API la consultan por igual; ninguna vista ramifica por
rol por su cuenta. Para cambiarla, se edita acá y listo.
"""

ADMIN = "admin"
COORDINADOR = "coordinador"
DELEGADO = "delegado"
FUNCIONARIO = "funcionario"
VERIFICADOR = "verificador"
CONSULTA = "consulta"

# Códigos de `Rol.codigo` que existen en el sistema.
ROLES = [ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR, CONSULTA]

# módulo -> {"lectura": set(roles), "escritura": set(roles)}
MATRIZ = {
    "atenciones": {
        "lectura": {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR, CONSULTA},
        "escritura": {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO},
    },
    "vecinos": {
        "lectura": {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR, CONSULTA},
        "escritura": {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO},
    },
    "delegaciones": {
        "lectura": {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR},
        "escritura": {ADMIN, COORDINADOR},
    },
    "metas": {
        "lectura": {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO},
        "escritura": {ADMIN, COORDINADOR, DELEGADO},
    },
    "tipos": {
        "lectura": {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR},
        "escritura": {ADMIN, COORDINADOR},
    },
    "subatenciones": {
        "lectura": {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR},
        "escritura": {ADMIN, COORDINADOR},
    },
    "usuarios": {
        "lectura": {ADMIN},
        "escritura": {ADMIN},
    },
    "roles": {
        "lectura": {ADMIN},
        "escritura": {ADMIN},
    },
}

# Modelo -> módulo. Las vistas web no repiten la asignación: la derivan del
# modelo que ya declaran.
MODELO_A_MODULO = {
    "Atencion": "atenciones",
    "Vecino": "vecinos",
    "Delegacion": "delegaciones",
    "Meta": "metas",
    "TipoAtencion": "tipos",
    "SubAtencion": "subatenciones",
    "Usuario": "usuarios",
    "Rol": "roles",
}


def codigo_de(usuario):
    """El código de rol del usuario. El superusuario cuenta como `admin`."""
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return None
    if usuario.is_superuser:
        return ADMIN
    return usuario.rol.codigo if usuario.rol_id else None


def puede(usuario, modulo, escritura=False):
    """¿El usuario puede leer (o escribir) ese módulo?"""
    codigo = codigo_de(usuario)
    if not codigo:
        return False
    permisos = MATRIZ.get(modulo)
    if not permisos:
        return False
    return codigo in permisos["escritura" if escritura else "lectura"]


def modulo_de(modelo):
    """El módulo de un modelo, o None si no está mapeado."""
    return MODELO_A_MODULO.get(modelo.__name__) if modelo else None


def modulos_de(usuario, escritura=False):
    """Los módulos que el usuario puede leer (o escribir)."""
    codigo = codigo_de(usuario)
    if not codigo:
        return set()
    clave = "escritura" if escritura else "lectura"
    return {modulo for modulo, p in MATRIZ.items() if codigo in p[clave]}
