"""Vistas compartidas por los mantenedores.

Cada módulo declara solo sus datos: el modelo, el formulario, el título, la
plantilla y los nombres de sus rutas. El comportamiento vive acá, una vez:
búsqueda, paginación, exportación a Excel y bitácora de auditoría.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import ProtectedError, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from apps.common.delegaciones import acotar, campo_delegacion_de
from apps.common.estados import ACTIVO, INACTIVO, ConEstado
from apps.common.permisos import modulo_de, puede
from apps.cumplimiento.auditoria import registrar


def resolver_campo(objeto, campo):
    """Saca el valor de un campo por ruta ("a.b") o llamando una función.

    Lo comparten la exportación a Excel y la vista de consulta: una sola forma
    de leer un campo, sin repetir el recorrido.
    """
    if callable(campo):
        return campo(objeto)
    valor = objeto
    for parte in campo.split("."):
        valor = getattr(valor, parte, "")
        if callable(valor):
            valor = valor()
    return "" if valor is None else str(valor)


class PermisoRequeridoMixin:
    """Exige el permiso del módulo según el rol, en la web.

    Va después de `LoginRequiredMixin`, así el anónimo se redirige al login y
    solo el usuario ya autenticado puede recibir un 403.
    """

    def dispatch(self, request, *args, **kwargs):
        modulo = modulo_de(getattr(self, "model", None))
        if modulo:
            escribir = request.method not in ("GET", "HEAD", "OPTIONS")
            if not puede(request.user, modulo, escritura=escribir):
                raise PermissionDenied(
                    "Tu rol no tiene permiso para este módulo."
                )
        return super().dispatch(request, *args, **kwargs)


class ExportarExcelMixin:
    """Descarga el listado en `.xlsx`.

    Reutiliza el mismo `get_queryset()` del listado, así respeta el filtro y
    exporta todas las páginas, no solo la que se está viendo.
    """

    # Cada columna es (encabezado, "ruta.atributo") o (encabezado, función).
    exportar_columnas = ()
    exportar_nombre = "listado"

    @property
    def permite_exportar(self):
        return bool(self.exportar_columnas)

    def exportar(self):
        from openpyxl import Workbook
        from openpyxl.utils import get_column_letter

        registrar(self.request, "exportar", None, f"Exportación: {self.titulo}")
        libro = Workbook()
        hoja = libro.active
        hoja.title = (self.titulo or "Listado")[:31]
        generado = timezone.localdate().strftime("%d-%m-%Y")
        hoja.append([f"{self.titulo or 'Listado'} · generado el {generado}"])
        hoja.append([encabezado for encabezado, _ in self.exportar_columnas])
        for fila in self.get_queryset():
            hoja.append(
                [resolver_campo(fila, campo) for _, campo in self.exportar_columnas]
            )
        for indice, (encabezado, _) in enumerate(self.exportar_columnas, start=1):
            letra = get_column_letter(indice)
            hoja.column_dimensions[letra].width = max(14, len(encabezado) + 4)
        respuesta = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )
        respuesta["Content-Disposition"] = (
            f'attachment; filename="{self.exportar_nombre}.xlsx"'
        )
        libro.save(respuesta)
        return respuesta


class Comun:
    """Datos que cada módulo define y que las plantillas necesitan."""

    titulo = ""
    subtitulo = ""
    seccion = ""
    etiqueta_nueva = ""
    url_listado = ""
    url_nueva = None  # solo el listado la define
    permite_exportar = False

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        modulo = modulo_de(getattr(self, "model", None))
        contexto.update(
            titulo=self.titulo,
            subtitulo=self.subtitulo,
            seccion=self.seccion,
            etiqueta_nueva=self.etiqueta_nueva,
            url_listado=self.url_listado,
            url_nueva=reverse(self.url_nueva) if self.url_nueva else "",
            permite_exportar=self.permite_exportar,
            # La plantilla oculta los botones de CRUD si el perfil no escribe.
            puede_escribir=bool(modulo)
            and puede(self.request.user, modulo, escritura=True),
        )
        return contexto


class AcotadoMixin:
    """Acota el queryset a la delegación activa, según el modelo.

    La ruta del campo la resuelve `delegaciones.campo_delegacion_de`: el
    acotamiento vale igual al listar, ver, editar, borrar y en las acciones, sin
    repetirlo por vista. Un rol de alcance global no se acota (`acotar` lo deja
    pasar). Un modelo sin campo de delegación (catálogos, configuración SGR) no
    se acota.
    """

    def acotar_queryset(self, queryset):
        return acotar(self.request, queryset, campo_delegacion_de(self.model))


class ListadoBase(
    AcotadoMixin, ExportarExcelMixin, Comun, LoginRequiredMixin, PermisoRequeridoMixin, ListView
):
    template_name = "listado.html"
    paginate_by = 8
    # Tamaños de página que ofrece el selector del listado (para ver más filas).
    tamanos_pagina = (8, 16, 32, 64)
    busqueda = ()
    # Llaves foráneas que la plantilla recorre. Traerlas con JOIN evita una
    # consulta por fila.
    relacionadas = ()
    # Los listados con datos personales dejan rastro en la bitácora.
    auditar_lectura = False

    def get_queryset(self):
        if hasattr(self.model, "todos"):
            queryset = self.model.todos.all()
        else:
            queryset = super().get_queryset()
        if self.relacionadas:
            queryset = queryset.select_related(*self.relacionadas)
        q = self.request.GET.get("q")
        if q and self.busqueda:
            condicion = Q()
            for campo in self.busqueda:
                condicion |= Q(**{f"{campo}__icontains": q})
            queryset = queryset.filter(condicion)
        # El alcance territorial se aplica en el servidor, sobre el mismo
        # queryset que exporta: un cambio de contexto actualiza ambas cosas.
        return self.acotar_queryset(queryset)

    def tamano_de_pagina(self):
        """El tamaño de página pedido en `?por=`, si es uno de los permitidos."""
        valor = self.request.GET.get("por")
        if valor and valor.isdigit() and int(valor) in self.tamanos_pagina:
            return int(valor)
        return self.paginate_by

    def get_paginate_by(self, queryset):
        return self.tamano_de_pagina()

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["tamanos_pagina"] = self.tamanos_pagina
        contexto["tamano_actual"] = self.tamano_de_pagina()
        return contexto

    def get(self, request, *args, **kwargs):
        if request.GET.get("exportar") and self.exportar_columnas:
            return self.exportar()
        if self.auditar_lectura:
            registrar(request, "ver", None, f"Listado: {self.titulo}")
        return super().get(request, *args, **kwargs)


class _FormularioBase(AcotadoMixin, Comun, LoginRequiredMixin, PermisoRequeridoMixin):
    template_name = "formulario.html"

    def get_queryset(self):
        # UpdateView acota el objeto a la delegación del usuario; un alta no usa
        # el queryset para el objeto.
        return self.acotar_queryset(super().get_queryset())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Los formularios acotan sus campos de delegación con la petición.
        kwargs["request"] = self.request
        return kwargs

    def get_template_names(self):
        # El modal pide el fragmento (X-Modal); sin ese encabezado se sirve la
        # página completa de siempre, que es la que ve quien no tiene JavaScript.
        if self.request.headers.get("X-Modal") == "1":
            return ["modal/formulario.html"]
        return [self.template_name]

    def get_success_url(self):
        return reverse(self.url_listado)


class AltaBase(_FormularioBase, CreateView):
    # Vacío = la vista concreta arma su propio aviso (por ejemplo, si además
    # manda un correo y quiere informar el resultado).
    mensaje_alta = "Registro creado."

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        registrar(self.request, "crear", self.object)
        if self.mensaje_alta:
            messages.success(self.request, self.mensaje_alta)
        return respuesta


class EdicionBase(_FormularioBase, UpdateView):
    def form_valid(self, form):
        respuesta = super().form_valid(form)
        registrar(self.request, "editar", self.object)
        messages.success(self.request, "Cambios guardados.")
        return respuesta


def marcar_vigencia(objeto, vigente):
    """Pone el registro en activo o inactivo, si tiene un estado binario.

    Solo aplica a los modelos cuyo `estado` es el par activo/inactivo
    (`ConEstado` y `Vecino`, que declara sus propios valores). Una `Atencion`
    usa `estado` para su ciclo de vida —ingresada, cerrada…—, así que no se
    toca: ahí la baja es solo la marca de `eliminado`.
    """
    if isinstance(objeto, ConEstado):
        objeto.estado = ACTIVO if vigente else INACTIVO
    elif hasattr(objeto, "ACTIVO") and hasattr(objeto, "INACTIVO"):
        objeto.estado = objeto.ACTIVO if vigente else objeto.INACTIVO
    if hasattr(objeto, "is_active"):
        objeto.is_active = vigente


class BorradoBase(AcotadoMixin, Comun, LoginRequiredMixin, PermisoRequeridoMixin, DeleteView):
    """Borra la fila de verdad. Solo si nadie la está usando.

    Es la acción destructiva: la contraparte reversible es `DesactivarBase`.
    """

    template_name = "confirmar.html"

    def get_queryset(self):
        if hasattr(self.model, "todos"):
            return self.acotar_queryset(self.model.todos.all())
        return self.acotar_queryset(super().get_queryset())

    def form_valid(self, form):
        objeto = self.object

        # Chequeo de negocio: da el mensaje más claro (qué la está usando).
        if hasattr(objeto, "esta_en_uso") and objeto.esta_en_uso():
            messages.error(
                self.request, f"No se puede eliminar: {objeto.motivo_en_uso()}"
            )
            return redirect(self.url_listado)

        try:
            objeto.delete()
        except ProtectedError as error:
            # Red de seguridad: la base también defiende las referencias, y acá
            # se traduce su error a un aviso entendible en vez de un 500.
            bloqueos = sorted(
                {str(vinculado._meta.verbose_name_plural) for vinculado in error.protected_objects}
            )
            messages.error(
                self.request,
                f"No se puede eliminar: lo usan {', '.join(bloqueos)}.",
            )
            return redirect(self.url_listado)

        registrar(self.request, "eliminar", objeto, "Eliminación definitiva.")
        messages.success(self.request, "Registro eliminado.")
        return redirect(self.url_listado)


class _AccionBase(AcotadoMixin, Comun, LoginRequiredMixin, PermisoRequeridoMixin, View):
    """Acción sobre un registro, por POST y sin formulario intermedio.

    La comparten desactivar y reactivar: cambian la vigencia del registro y
    vuelven al listado. La confirmación la pide el botón, en el navegador.
    """

    detalle = ""
    mensaje = ""

    def post(self, request, pk, *args, **kwargs):
        objeto = self.get_objeto(pk)
        self.aplicar(objeto)
        objeto.save()
        registrar(request, "editar", objeto, self.detalle)
        messages.success(request, f"{self.titulo or 'Registro'} {self.mensaje}.")
        return redirect(self.url_listado)

    def get_objeto(self, pk):
        # `todos` para llegar también a un registro ya desactivado; y acotado a
        # la delegación del usuario, para no tocar un registro ajeno.
        gestor = getattr(self.model, "todos", self.model.objects)
        return get_object_or_404(self.acotar_queryset(gestor.all()), pk=pk)


class DesactivarBase(_AccionBase):
    """Saca el registro de circulación sin borrarlo. Siempre es posible.

    La fila queda marcada con `eliminado`, así que desaparece de los
    desplegables y de las referencias nuevas, pero sigue visible en el listado
    y se puede revertir con `ReactivarBase`.
    """

    detalle = "Desactivación de registro."
    mensaje = "desactivado"

    def aplicar(self, objeto):
        objeto.eliminar()
        marcar_vigencia(objeto, False)


class ReactivarBase(_AccionBase):
    """Devuelve el registro a circulación."""

    detalle = "Reactivación de registro."
    mensaje = "reactivado"

    def aplicar(self, objeto):
        if hasattr(objeto, "eliminado"):
            objeto.eliminado = None
        marcar_vigencia(objeto, True)


class ConsultaBase(AcotadoMixin, Comun, LoginRequiredMixin, PermisoRequeridoMixin, DetailView):
    """Ficha de solo lectura de un registro.

    Completa el CRUD: el PDF pide crear, **consultar**, listar, editar y
    eliminar. Usa el mismo permiso de lectura del listado, porque no cambia
    nada. Se sirve como página completa y, con el encabezado del modal, como
    fragmento para el `<dialog>`.
    """

    template_name = "consulta.html"
    # Cada campo es (etiqueta, "ruta.atributo") o (etiqueta, función).
    consulta_campos = ()
    # Orígenes del paso manual al tubo: (origen, etiqueta) de `tubo:enviar`.
    consulta_tubo = ()

    def get_queryset(self):
        return self.acotar_queryset(super().get_queryset())

    def get_template_names(self):
        if self.request.headers.get("X-Modal") == "1":
            return ["modal/consulta.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["campos"] = [
            (etiqueta, resolver_campo(self.object, campo))
            for etiqueta, campo in self.consulta_campos
        ]
        contexto["acciones_tubo"] = [
            {
                "url": reverse("tubo:enviar", args=[origen, self.object.pk]),
                "etiqueta": etiqueta,
            }
            for origen, etiqueta in self.consulta_tubo
        ]
        return contexto
