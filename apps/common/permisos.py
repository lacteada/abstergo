"""Autorización por rol, en un solo lugar.

La matriz dice, por módulo, qué roles pueden **leer** y qué roles pueden
**escribir**. La web y la API la consultan por igual; ninguna vista ramifica por
rol por su cuenta. Para cambiarla, se edita acá y listo.

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

# Los que ven por encima de las delegaciones: no se acotan a un territorio.
ALCANCE_GLOBAL = {ADMIN, COORDINADOR}

TODOS = set(ROLES)
GESTION = {ADMIN, COORDINADOR}
TERRENO = {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO}
CATALOGOS = {ADMIN, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR}

# módulo -> {"read": set(roles), "write": set(roles)}
MATRIZ = {
    "cases": {"read": TODOS, "write": TERRENO},
    "neighbors": {"read": TODOS, "write": TERRENO},
    "delegations": {"read": CATALOGOS, "write": GESTION},
    "goals": {"read": TERRENO, "write": {ADMIN, COORDINADOR, DELEGADO}},
    "attention_types": {"read": CATALOGOS, "write": GESTION},
    "attention_subtypes": {"read": CATALOGOS, "write": GESTION},
    "users": {"read": {ADMIN}, "write": {ADMIN}},
    "roles": {"read": {ADMIN}, "write": {ADMIN}},
}

# Modelo -> módulo. Las vistas web no repiten la asignación: la derivan del
# modelo que ya declaran.
MODELO_A_MODULO = {
    "Atencion": "cases",
    "Vecino": "neighbors",
    "Delegacion": "delegations",
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


def puede(usuario, modulo, escritura=False):
    """¿El usuario puede leer (o escribir) ese módulo?"""
    codigo = codigo_de(usuario)
    permisos = MATRIZ.get(modulo) if codigo else None
    if not permisos:
        return False
    return codigo in permisos["write" if escritura else "read"]


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
    """Los módulos que el usuario puede leer (o escribir)."""
    codigo = codigo_de(usuario)
    if not codigo:
        return set()
    clave = "write" if escritura else "read"
    return {modulo for modulo, p in MATRIZ.items() if codigo in p[clave]}
