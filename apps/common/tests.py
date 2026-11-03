"""Pruebas de la matriz de permisos."""

import pytest

from apps.common.permisos import MATRIZ, modulos_de, puede


class UsuarioFalso:
    """Lo mínimo que la matriz necesita de un usuario."""

    def __init__(self, codigo=None, superuser=False, cargo=None):
        self.is_authenticated = True
        self.is_superuser = superuser
        self.rol_id = 1 if codigo else None
        self.rol = type("Rol", (), {"codigo": codigo})()
        self.cargo_id = 1 if cargo else None
        self.cargo = type("Cargo", (), {"codigo": cargo})()


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


# --------------------------------------------------------------------- Cargo
def test_el_cargo_suma_permisos_al_rol():
    # Un rol sin permisos operativos (consulta) más un cargo de delegación.
    usuario = UsuarioFalso("consulta", cargo="gestor-social")
    assert puede(usuario, "cases", escritura=True) is True
    assert puede(usuario, "neighbors", escritura=True) is True
    assert puede(usuario, "goals", escritura=True) is False


def test_el_cargo_no_abre_modulos_de_administracion():
    usuario = UsuarioFalso("consulta", cargo="gestor-social")
    assert puede(usuario, "positions") is False
    assert puede(usuario, "roles") is False


def test_los_modulos_unen_rol_y_cargo():
    usuario = UsuarioFalso("funcionario", cargo="gestor-social")
    modulos = modulos_de(usuario, escritura=True)
    assert "cases" in modulos  # por rol y por cargo
    assert "neighbors" in modulos  # solo por el cargo (gestor social)
    assert "goals" not in modulos


def test_sin_cargo_no_cambia_nada():
    assert modulos_de(UsuarioFalso("funcionario")) == modulos_de(
        UsuarioFalso("funcionario", cargo=None)
    )


def test_el_supervisor_lee_todo_y_solo_escribe_metas():
    usuario = UsuarioFalso("coordinador")
    assert modulos_de(usuario) == set(MATRIZ)
    assert modulos_de(usuario, escritura=True) == {"goals"}
    assert puede(usuario, "users") is True
    assert puede(usuario, "goals", escritura=True) is True
    assert puede(usuario, "cases", escritura=True) is False
    assert puede(usuario, "roles", escritura=True) is False


def test_el_delegado_gestiona_atenciones_y_vecinos():
    usuario = UsuarioFalso("delegado")
    assert puede(usuario, "cases", escritura=True) is True
    assert puede(usuario, "neighbors", escritura=True) is True
    assert puede(usuario, "users") is False
    assert puede(usuario, "roles") is False
