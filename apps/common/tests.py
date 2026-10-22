"""Pruebas de la matriz de permisos."""

import pytest

from apps.common.permisos import MATRIZ, modulos_de, puede


class UsuarioFalso:
    """Lo mínimo que la matriz necesita de un usuario."""

    def __init__(self, codigo=None, superuser=False):
        self.is_authenticated = True
        self.is_superuser = superuser
        self.rol_id = 1 if codigo else None
        self.rol = type("Rol", (), {"codigo": codigo})()


@pytest.mark.parametrize(
    "codigo, esperado",
    [("admin", True), ("coordinador", False), ("funcionario", True), ("consulta", False)],
)
def test_escritura_de_vecinos_segun_rol(codigo, esperado):
    assert puede(UsuarioFalso(codigo), "neighbors", escritura=True) is esperado


def test_anonimo_no_puede_nada():
    assert not puede(None, "neighbors")


def test_el_superusuario_cuenta_como_admin():
    usuario = UsuarioFalso(superuser=True)
    assert modulos_de(usuario) == set(MATRIZ)
    assert modulos_de(usuario, escritura=True) == set(MATRIZ)


def test_consulta_no_tiene_modulos():
    assert modulos_de(UsuarioFalso("consulta")) == set()
    assert modulos_de(UsuarioFalso("consulta"), escritura=True) == set()
