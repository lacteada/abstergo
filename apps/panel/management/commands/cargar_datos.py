"""Carga los JSON de datos_nuevos/ en la base de datos usando el ORM.

Es reejecutable: usa update_or_create, así que correrlo dos veces deja los
mismos conteos.

Además de los maestros, al final siembra **volumen demo** (atenciones, casos,
compromisos, organizaciones y la matriz SGR) para que los paneles y tableros se
vean con datos reales. El volumen se genera una sola vez por base: si ya hay
atenciones o gestiones, el paso se omite (no duplica ni borra nada).
"""

import json
import random
from datetime import timedelta
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.atenciones.models import Atencion
from apps.casos.models import CasoSocial, Llamada
from apps.catalogos.models import Meta, SubAtencion, TipoAtencion
from apps.ciudadanos.models import Vecino
from apps.common.validators import normalizar_rut
from apps.comunidad.models import Organizacion
from apps.cuentas.models import Rol, Usuario
from apps.organizacion.models import Cargo, Delegacion, Territorio
from apps.sgr.models import (
    AjusteConducta,
    Area,
    Ausencia,
    Evidencia,
    Indicador,
    MetaIndicador,
    Periodo,
    RegistroGestion,
    Validacion,
)
from apps.tubo.models import Carta, TareaTubo

DATOS = Path(settings.BASE_DIR) / "datos_nuevos"

# Semilla única: la misma base produce el mismo volumen, sin duplicar.
SEMILLA_VOLUMEN = 2026

BARRIOS = (
    "Los Aromos",
    "Balmaceda",
    "El Roble",
    "Las Palmeras",
    "San Juan",
    "Vista Hermosa",
    "Los Nogales",
    "El Mirador",
    "La Colina",
    "Los Pinos",
    "Ampliación Norte",
    "Las Dunas",
)

MOTIVOS = (
    "Solicita información de trámites municipales",
    "Requiere apoyo social para su familia",
    "Reporta un problema en el espacio público",
    "Solicita mediación por conflicto vecinal",
    "Pide informe social para un beneficio",
    "Consulta por subsidios previsionales",
)

DETALLES = (
    "Se entrega orientación y se agenda seguimiento en terreno.",
    "Se recopilan antecedentes y se deriva al área correspondiente.",
    "Se coordina visita con la organización del sector.",
    "Se registra la solicitud y se compromete respuesta en el plazo.",
    "Se gestiona el beneficio y se informa al vecino el resultado.",
)

# (nombre, grupo, unidad) de los indicadores de la matriz demo.
INDICADORES_DEMO = (
    ("Atenciones ciudadanas", "apoyo-administrativo", "gestiones"),
    ("Registro de atenciones", "apoyo-administrativo", "gestiones"),
    ("Visitas a organizaciones", "territorial-oocc", "gestiones"),
    ("Organizaciones con vigencia al día", "territorial-oocc", "porcentaje"),
    ("Operativos de limpieza", "coordinador-servicios", "gestiones"),
    ("Denuncias canalizadas", "coordinador-servicios", "gestiones"),
    ("Casos sociales en seguimiento", "gestor-social", "gestiones"),
    ("Informes sociales emitidos", "gestor-social", "gestiones"),
    ("Compras tramitadas", "planificacion-control", "gestiones"),
    ("Plan anual de compras controlado", "planificacion-control", "porcentaje"),
    ("Rondas comunitarias", "seguridad", "gestiones"),
    ("Charlas de autocuidado", "seguridad", "gestiones"),
)

# cargo -> grupo de la matriz.
GRUPO_POR_CARGO = {
    "delegado": "territorial-oocc",
    "gestor-social": "gestor-social",
    "apoyo-administrativo": "apoyo-administrativo",
    "organizaciones-comunitarias": "territorial-oocc",
    "gestor-de-compras-y-proyectos": "planificacion-control",
    "gestion-y-planificacion": "planificacion-control",
    "coordinador-de-servicios-comunitarios": "coordinador-servicios",
}


def leer(nombre):
    with (DATOS / f"{nombre}.json").open(encoding="utf-8") as archivo:
        return json.load(archivo)


class Command(BaseCommand):
    help = "Carga datos_nuevos/ y siembra volumen demo. Reejecutable sin duplicar."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.creados = 0
        self.actualizados = 0

    def anotar(self, creado):
        if creado:
            self.creados += 1
        else:
            self.actualizados += 1

    def cargar(self, archivo, modelo, clave, armar):
        """Recorre un archivo y escribe con update_or_create.

        Las entidades tienen borrado lógico, así que usa el gestor sin filtro
        (`todos`) y limpia `eliminado`: recargar el JSON restaura lo dado de
        baja en vez de chocar contra el campo único.
        """
        for fila in leer(archivo):
            valores = armar(fila)
            valores["eliminado"] = None
            _, creado = modelo.todos.update_or_create(
                **{clave: fila[clave]},
                defaults=valores,
            )
            self.anotar(creado)

    @transaction.atomic
    def handle(self, *args, **options):
        self.cargar(
            "delegaciones",
            Delegacion,
            "codigo",
            lambda f: {
                "nombre": f["nombre"],
                "direccion": f["direccion"],
                "comuna": f["comuna"],
                "estado": f.get("estado", "activo"),
            },
        )
        self.cargar(
            "roles",
            Rol,
            "codigo",
            lambda f: {"nombre": f["nombre"], "descripcion": f["descripcion"]},
        )
        self.cargar(
            "cargos",
            Cargo,
            "codigo",
            lambda f: {
                "nombre": f["nombre"],
                "descripcion": f["descripcion"],
                "funciones": f.get("funciones", ""),
            },
        )
        self.cargar_usuarios()
        self.cargar(
            "metas",
            Meta,
            "codigo",
            lambda f: {
                "nombre": f["nombre"],
                "descripcion": f["descripcion"],
                "delegacion": Delegacion.objects.get(codigo=f["delegacion"]),
                "estado": f.get("estado", "activo"),
            },
        )
        self.cargar(
            "tipos_atencion",
            TipoAtencion,
            "codigo",
            lambda f: {
                "nombre": f["nombre"],
                "descripcion": f["descripcion"],
                "estado": f.get("estado", "activo"),
            },
        )
        self.cargar(
            "sub_atenciones",
            SubAtencion,
            "codigo",
            lambda f: {
                "nombre": f["nombre"],
                "tipo_atencion": TipoAtencion.objects.get(nombre=f["tipo_atencion"]),
                "forma": f.get("forma", ""),
                "estado": f.get("estado", "activo"),
            },
        )
        self.cargar(
            "vecinos",
            Vecino,
            "rut",
            lambda f: {
                "nombre": f["nombre"],
                "rut": normalizar_rut(f["rut"]),
                "direccion": f["direccion"],
                "telefono": f["telefono"],
                "territorio": Delegacion.objects.get(codigo=f["territorio"]),
                "tipo_gestion": f["tipo_gestion"],
                "estado": f["estado"],
            },
        )
        self.cargar_volumen()
        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {self.creados} creados, {self.actualizados} actualizados."
            )
        )

    def cargar_usuarios(self):
        """El rol, el cargo y la delegación van en el propio usuario.

        La llave de idempotencia es el nombre completo, no el correo: un
        usuario sin correo lo tiene nulo y no sirve para buscar. Sin correo la
        contraseña queda inutilizable, porque ese usuario no puede entrar.

        `superusuario` en el JSON da acceso al Django Admin (tablas de la ley);
        sin la bandera, el usuario es solo de la aplicación.
        """
        for fila in leer("usuarios"):
            nombre, _, apellido = fila["nombre"].partition(" ")
            correo = fila.get("email") or None
            superusuario = bool(fila.get("superusuario", False))
            cargo = (
                Cargo.objects.filter(codigo=fila["cargo"]).first()
                if fila.get("cargo")
                else None
            )
            usuario, creado = Usuario.objects.update_or_create(
                first_name=nombre,
                last_name=apellido,
                defaults={
                    "email": correo,
                    "rol": Rol.objects.get(nombre=fila["rol"]),
                    "cargo": cargo,
                    "delegacion": Delegacion.objects.get(codigo=fila["delegacion"]),
                    "is_active": fila["activo"],
                    "is_staff": superusuario,
                    "is_superuser": superusuario,
                    "eliminado": None,
                },
            )
            if creado:
                usuario.set_password(
                    settings.USUARIOS_PASSWORD_INICIAL if correo else None
                )
                usuario.save()
            # La semilla manda: se fija la lista completa de autorizadas, así
            # reejecutar deja el contexto igual y no arrastra una lista vieja.
            usuario.delegaciones_autorizadas.set(
                Delegacion.objects.filter(codigo__in=fila.get("delegaciones") or [])
            )
            self.anotar(creado)

    # --------------------------------------------------------- Volumen demo
    def cargar_volumen(self):
        """Siembra datos transaccionales una sola vez por base de datos."""
        if Atencion.objects.exists() or RegistroGestion.objects.exists():
            self.stdout.write("Volumen demo ya presente; se omite.")
            return
        rnd = random.Random(SEMILLA_VOLUMEN)
        self.cargar_territorios()
        call_command(
            "generar_vecinos",
            cantidad=60,
            semilla=SEMILLA_VOLUMEN,
            stdout=StringIO(),
        )
        self.cargar_organizaciones(rnd)
        self.cargar_atenciones(rnd)
        self.cargar_casos(rnd)
        self.cargar_llamadas(rnd)
        self.cargar_tareas(rnd)
        self.cargar_cartas(rnd)
        self.cargar_sgr(rnd)
        call_command("generar_alertas", stdout=StringIO())
        self.stdout.write(self.style.SUCCESS("Volumen demo cargado."))

    def cargar_territorios(self):
        for delegacion in Delegacion.objects.all():
            for indice in range(1, 3):
                Territorio.todos.update_or_create(
                    codigo=f"{delegacion.codigo}-{indice}",
                    defaults={
                        "nombre": f"{delegacion.nombre} — Sector {indice}",
                        "delegacion": delegacion,
                        "estado": "activo",
                        "eliminado": None,
                    },
                )

    def _usuarios_por_delegacion(self, roles):
        """Agrupa los usuarios de ciertos roles por delegación id."""
        usuarios = list(
            Usuario.vigentes()
            .filter(is_active=True, rol__codigo__in=roles)
            .select_related("delegacion")
        )
        por_delegacion = {}
        for usuario in usuarios:
            por_delegacion.setdefault(usuario.delegacion_id, []).append(usuario)
        return por_delegacion, usuarios

    def cargar_organizaciones(self, rnd):
        delegaciones = list(Delegacion.objects.all())
        subtipos = [
            "adulto-mayor",
            "deportiva",
            "centro-madres-cultural-juvenil",
            "comite",
            "otro",
        ]
        for indice in range(1, 26):
            delegacion = rnd.choice(delegaciones)
            Organizacion.todos.update_or_create(
                codigo=f"jjvv-{indice:02d}",
                defaults={
                    "nombre": f"Junta de Vecinos {rnd.choice(BARRIOS)} {indice}",
                    "domicilio_legal": f"{rnd.choice(BARRIOS)} {rnd.randint(10, 900)}",
                    "territorio": delegacion,
                    "tipo": rnd.choice(["territorial", "funcional"]),
                    "subtipo": rnd.choice(subtipos),
                    "situacion": "vigente",
                    "verificacion": rnd.choice(["verificada", "sin-verificar"]),
                    "socios_activos": rnd.randint(12, 180),
                    "fecha_constitucion": timezone.localdate()
                    - timedelta(days=rnd.randint(400, 6000)),
                    "eliminado": None,
                },
            )

    def cargar_atenciones(self, rnd):
        vecinos = list(Vecino.objects.select_related("territorio").all())
        tipos = list(TipoAtencion.objects.all())
        subs_por_tipo = {}
        for sub in SubAtencion.objects.all():
            subs_por_tipo.setdefault(sub.tipo_atencion_id, []).append(sub)
        por_delegacion, todos = self._usuarios_por_delegacion(
            ["funcionario", "delegado"]
        )
        estados = ["cerrada", "en_proceso", "ingresada", "derivada"]
        pesos = [55, 22, 13, 10]
        for indice in range(300):
            vecino = rnd.choice(vecinos)
            delegacion = vecino.territorio
            tipo = rnd.choice(tipos)
            subs = subs_por_tipo.get(tipo.pk, [])
            funcionarios = por_delegacion.get(delegacion.pk) or todos or [None]
            dias = 0 if indice < 8 else rnd.randint(0, 59)
            Atencion.objects.create(
                vecino=vecino,
                tipo_atencion=tipo,
                sub_atencion=rnd.choice(subs) if subs else None,
                delegacion=delegacion,
                funcionario=rnd.choice(funcionarios),
                fecha=timezone.now() - timedelta(days=dias, minutes=rnd.randint(0, 600)),
                motivo=rnd.choice(MOTIVOS),
                detalle=rnd.choice(DETALLES),
                estado=rnd.choices(estados, weights=pesos)[0],
                canal=rnd.choice(["presencial", "telefono", "web"]),
            )

    def cargar_casos(self, rnd):
        por_delegacion, todos = self._usuarios_por_delegacion(
            ["funcionario", "delegado"]
        )
        vecinos = list(Vecino.objects.all())
        elegidos = rnd.sample(vecinos, min(20, len(vecinos)))
        for vecino in elegidos:
            responsable = rnd.choice(
                por_delegacion.get(vecino.territorio_id) or todos or [None]
            )
            caso = CasoSocial.objects.create(
                vecino=vecino,
                responsable=responsable,
                fecha_apertura=timezone.localdate() - timedelta(days=rnd.randint(5, 90)),
                motivo=rnd.choice(MOTIVOS),
                estado=rnd.choice(["abierto", "seguimiento", "cerrado"]),
                observaciones=rnd.choice(DETALLES),
            )
            atenciones = list(
                Atencion.objects.filter(vecino=vecino).order_by("fecha")[:3]
            )
            for atencion in atenciones:
                atencion.caso = caso
                atencion.save(update_fields=["caso"])

    def cargar_llamadas(self, rnd):
        atenciones = list(Atencion.objects.order_by("?")[:40])
        for atencion in atenciones:
            estado = rnd.choices(
                ["pendiente", "realizada", "anulada"], weights=[50, 40, 10]
            )[0]
            Llamada.objects.create(
                vecino=atencion.vecino,
                atencion=atencion,
                motivo=rnd.choice(MOTIVOS),
                fecha_programada=timezone.localdate() + timedelta(days=rnd.randint(-10, 20)),
                estado=estado,
                fecha_realizada=(
                    timezone.now() - timedelta(days=rnd.randint(0, 15))
                    if estado == "realizada"
                    else None
                ),
                realizada_por=atencion.funcionario if estado == "realizada" else None,
            )

    def cargar_tareas(self, rnd):
        delegaciones = list(Delegacion.objects.all())
        territorios_por_delegacion = {}
        for territorio in Territorio.objects.all():
            territorios_por_delegacion.setdefault(territorio.delegacion_id, []).append(
                territorio
            )
        por_delegacion, todos = self._usuarios_por_delegacion(
            ["funcionario", "delegado"]
        )
        hoy = timezone.localdate()
        for indice in range(60):
            delegacion = rnd.choice(delegaciones)
            territorios = territorios_por_delegacion.get(delegacion.pk) or [None]
            responsable = rnd.choice(por_delegacion.get(delegacion.pk) or todos or [None])
            TareaTubo.objects.create(
                titulo=f"{rnd.choice(MOTIVOS)}",
                descripcion=rnd.choice(DETALLES),
                estado=rnd.choices(
                    ["ingresada", "pendiente", "en_proceso", "realizada"],
                    weights=[20, 25, 30, 25],
                )[0],
                delegacion=delegacion,
                territorio=rnd.choice(territorios),
                tipo=rnd.choice(["externo", "interno"]),
                solicitante=rnd.choice(["Vecino", "Delegación", "Organización"]),
                responsable=responsable,
                avance=rnd.choice([0, 15, 30, 50, 75, 100]),
                fecha_ingreso=timezone.now() - timedelta(days=rnd.randint(1, 60)),
                fecha_compromiso=hoy + timedelta(days=rnd.randint(-35, 35)),
                orden=indice,
            )

    def cargar_cartas(self, rnd):
        delegaciones = list(Delegacion.objects.all())
        por_delegacion, todos = self._usuarios_por_delegacion(
            ["funcionario", "delegado"]
        )
        for indice in range(1, 16):
            delegacion = rnd.choice(delegaciones)
            encargado = rnd.choice(por_delegacion.get(delegacion.pk) or todos or [None])
            Carta.objects.create(
                asunto=f"Solicitud ciudadana {indice}",
                correlativo=indice,
                destinatario=rnd.choice(["alcaldesa", "delegado"]),
                remitente=rnd.choice(["Junta de Vecinos", "Vecino particular"]),
                contacto=f"+56 9 {rnd.randint(1000, 9999)} {rnd.randint(1000, 9999)}",
                fecha=timezone.localdate() - timedelta(days=rnd.randint(0, 60)),
                encargado=encargado,
                delegacion=delegacion,
                estado=rnd.choice(["en_proceso", "aprobada", "finalizada", "no_aplica"]),
                observacion=rnd.choice(DETALLES),
            )

    def cargar_sgr(self, rnd):
        hoy = timezone.localdate()
        periodo, _ = Periodo.todos.update_or_create(
            codigo="demo-2026",
            defaults={
                "nombre": "Período demo 2026",
                "inicio": hoy - timedelta(days=120),
                "termino": hoy + timedelta(days=60),
                "situacion": "abierto",
                "eliminado": None,
            },
        )
        delegaciones = list(Delegacion.objects.all())
        por_cargo = {}
        for usuario in Usuario.vigentes().filter(is_active=True, cargo__isnull=False):
            por_cargo.setdefault(usuario.cargo_id, []).append(usuario)
        _, funcionarios = self._usuarios_por_delegacion(["funcionario", "delegado"])

        areas = []
        for indice, cargo in enumerate(Cargo.objects.all()):
            delegacion = delegaciones[indice % len(delegaciones)]
            responsable = rnd.choice(
                por_cargo.get(cargo.pk) or funcionarios or [None]
            )
            area, _ = Area.todos.update_or_create(
                codigo=f"area-{cargo.codigo}",
                defaults={
                    "nombre": cargo.nombre,
                    "grupo": GRUPO_POR_CARGO.get(cargo.codigo, "apoyo-administrativo"),
                    "cargo": cargo,
                    "responsable": responsable,
                    "delegacion": delegacion,
                    "eliminado": None,
                },
            )
            areas.append(area)

        indicadores = []
        for indice, (nombre, grupo, unidad) in enumerate(INDICADORES_DEMO, start=1):
            indicador, _ = Indicador.todos.update_or_create(
                codigo=f"ind-{indice:02d}",
                defaults={
                    "nombre": nombre,
                    "grupo": grupo,
                    "unidad": unidad,
                    "tipo_calculo": "conteo" if unidad == "gestiones" else "razon",
                    "eliminado": None,
                },
            )
            indicadores.append(indicador)

        metas = []
        for area in areas:
            del_grupo = [i for i in indicadores if i.grupo == area.grupo]
            elegidos = del_grupo[:3] or indicadores[:2]
            ponderador = round(1 / len(elegidos), 3)
            for indicador in elegidos:
                meta, _ = MetaIndicador.todos.update_or_create(
                    periodo=periodo,
                    area=area,
                    indicador=indicador,
                    defaults={
                        "ponderador": ponderador,
                        "meta": rnd.choice([20, 30, 40, 50, 60]),
                        "funcionario": area.responsable,
                        "eliminado": None,
                    },
                )
                metas.append(meta)

        organizaciones = list(Organizacion.objects.all())
        registros = []
        for indice in range(320):
            meta = rnd.choice(metas)
            area = meta.area
            funcionario = area.responsable or rnd.choice(funcionarios or [None])
            dias = 0 if indice < 10 else rnd.randint(0, 40)
            actividad = rnd.choice(["", "", "visita", "reunion", "taller"])
            organizacion = None
            if actividad == "visita":
                candidatas = [
                    o
                    for o in organizaciones
                    if o.territorio_id == area.delegacion_id
                ]
                organizacion = rnd.choice(candidatas) if candidatas else None
            registro = RegistroGestion.objects.create(
                fecha=max(periodo.inicio, hoy - timedelta(days=dias)),
                area=area,
                indicador=meta.indicador,
                funcionario=funcionario,
                cantidad=rnd.randint(1, 3),
                detalle=rnd.choice(DETALLES),
                etapa="ejecutada",
                tipo_solicitante="externo",
                contacto_nombre=rnd.choice(["Ana", "Luis", "Rosa", "Juan", "María"]),
                contacto_telefono=f"+56 9 {rnd.randint(1000, 9999)} {rnd.randint(1000, 9999)}",
                estado=rnd.choices(["registrada", "aprobada"], weights=[70, 30])[0],
                accion=rnd.choice(MOTIVOS),
                actividad=actividad,
                organizacion=organizacion,
            )
            registros.append(registro)

        verificador = (
            Usuario.vigentes().filter(rol__codigo="verificador", is_active=True).first()
        )
        for indice, registro in enumerate(registros[:15]):
            evidencia = Evidencia.objects.create(
                registro=registro,
                archivo=f"evidencias/demo-{indice:02d}.pdf",
                autor=registro.funcionario,
                tipo="informe",
                tamano=rnd.randint(40_000, 900_000),
                huella=f"{rnd.getrandbits(64):016x}",
                estado_revision="pendiente",
            )
            if verificador and verificador.pk != registro.funcionario_id and indice < 8:
                decision = rnd.choice(["aprobada", "aprobada", "rechazada", "correccion"])
                Validacion.objects.create(
                    evidencia=evidencia,
                    verificador=verificador,
                    decision=decision,
                    observacion=rnd.choice(DETALLES),
                    fecha=timezone.now() - timedelta(hours=rnd.randint(0, 48)),
                )

        for area in areas:
            if rnd.random() < 0.6:
                AjusteConducta.objects.create(
                    area=area,
                    tipo=rnd.choice(["reclamo", "felicitacion"]),
                    fecha=hoy - timedelta(days=rnd.randint(0, 60)),
                    respaldo=f"Respaldo {rnd.randint(1, 999)}" if rnd.random() < 0.5 else "",
                    medio=rnd.choice(["oficio", "correo", "presencial", "otro"]),
                    periodo=periodo,
                )
            if rnd.random() < 0.3:
                desde = hoy - timedelta(days=rnd.randint(3, 30))
                Ausencia.objects.create(
                    area=area,
                    periodo=periodo,
                    tipo=rnd.choice(["licencia", "vacaciones", "emergencia", "compensatorio"]),
                    desde=desde,
                    hasta=desde + timedelta(days=rnd.randint(1, 5)),
                    registrada_por=area.responsable,
                )
