# Diseño de Mockups — Sistema Municipal de Gestión de Atención Ciudadana

> Documento puramente estético/estructural. Describe el **orden y jerarquía visual de conceptos y assets** de cada pantalla tal como aparecen en el mockup, sin asumir ni deducir el framework, librería o tecnología que se usará para implementarlos.

---

## 0. Elementos globales recurrentes

Estos elementos se repiten en todas las pantallas internas (posteriores al login) y deben mantener el mismo orden y posición relativa en cada vista.

### 0.1 Barra lateral izquierda (sidebar)
Orden de arriba hacia abajo:
1. **Bloque de marca** (fila superior de la barra lateral)
   - Icono/placeholder de imagen cuadrado (logo)
   - Texto "Sistema Municipal" (título de marca)
2. **Ítem de navegación: Inicio**
   - Icono de casa + etiqueta "Inicio"
3. **Grupo colapsable: Mantenedores**
   - Icono de personas/engranaje + etiqueta "Mantenedores" + flecha/chevron de expansión (▲/▼)
   - Sub-ítems anidados (con sangría), en este orden:
     1. Delegaciones Municipales
     2. Usuarios
     3. Roles
     4. Metas
     5. Tipo de Atención
     6. Sub Atención
     7. Atenciones
     8. Tipo de Gestión
     9. Vecinos
4. **Ítem de navegación: Reportes**
   - Icono de gráfico de barras + etiqueta "Reportes"

Estado visual: el ítem/sub-ítem correspondiente a la pantalla activa se muestra resaltado (fondo distinto / texto en color de énfasis).

### 0.2 Barra superior (header)
Orden de izquierda a derecha:
1. Espacio vacío / área de título de página (queda a cargo del contenido central)
2. **Bloque de usuario** (extremo derecho):
   - Icono circular de avatar (placeholder de persona)
   - Texto "Usuario Administrador"
   - Flecha/chevron desplegable (▼)

### 0.3 Barra de ventana (chrome decorativo)
En algunas pantallas aparece una barra superior tipo "ventana de escritorio":
- Tres círculos decorativos (semáforo de ventana) alineados a la izquierda
- Texto de la ruta/nombre de pantalla (ej. "Sistema Municipal - Validar código") centrado o a continuación de los círculos

### 0.4 Patrón de vista "Listado" (Mantenedores)
Todas las pantallas de mantenedores (Roles, Usuarios, Delegaciones Municipales, Metas, Tipo de Atención, Sub Atención, Vecinos) comparten el mismo orden de bloques en el área de contenido, de arriba hacia abajo:
1. **Título de la sección** (texto grande, ej. "Roles", "Usuarios")
   - Subtítulo opcional debajo del título (ej. "CRUD de vecinos")
2. **Fila de acción superior**, alineada horizontalmente:
   - Izquierda: **campo de búsqueda** con icono de lupa + placeholder "Buscar..."
   - Derecha: **botón primario** de color sólido con icono "+" y etiqueta "Nuevo [Entidad]" (ej. "+ Nuevo Rol", "+ Nuevo Usuario", "+ Nueva Delegación", "+ Nueva Meta", "+ Nuevo Tipo", "+ Nueva Sub Atención", "+ Nuevo Vecino")
3. **Tabla de datos**, con:
   - Encabezado de columnas (fila con fondo diferenciado)
   - Filas de datos alternadas o con líneas divisorias
   - Última columna siempre: **"Acciones"**, con dos iconos por fila:
     - Icono de lápiz (editar)
     - Icono de basurero en color de alerta (eliminar)

---

## 1. Pantalla: Login

Orden de arriba hacia abajo, dentro de una tarjeta centrada:
1. Encabezado de contenedor: texto "Login" (fuera/encima de la tarjeta, a modo de etiqueta de pantalla)
2. **Tarjeta con borde**, contenido centrado:
   1. Placeholder de imagen (logo, cuadrado con icono de montaña/sol genérico)
   2. Título "Sistema Municipal" (texto grande, en negrita)
   3. Subtítulo "Gestión de Atención Ciudadana" (texto secundario, más pequeño)
   4. Campo de texto "Usuario" con icono de persona a la izquierda
   5. Campo de texto "Contraseña" con icono de candado a la izquierda
   6. Botón primario de ancho completo, color sólido (azul), texto "Ingresar"
   7. Enlace de texto centrado, subrayado/color de link: "¿Olvidaste tu contraseña?"

---

## 2. Pantalla: Recuperar contraseña

1. Etiqueta de pantalla "Recuperar contraseña" (fuera de la tarjeta)
2. **Tarjeta con borde**, contenido centrado:
   1. Placeholder de imagen (logo)
   2. Título "Sistema Municipal"
   3. Subtítulo "Gestión de Atención Ciudadana"
   4. Texto explicativo centrado: "Ingresa tu correo electrónico y te enviaremos las instrucciones para recuperar tu contraseña."
   5. Campo de texto "Correo electrónico" con icono de sobre/mail a la izquierda
   6. Botón primario de ancho completo, texto "Enviar instrucciones"
   7. Enlace de texto centrado: "Volver al login"

---

## 3. Pantalla: Validar código

Contenida dentro de una ventana con barra decorativa superior (3 círculos + texto "Sistema Municipal - Validar código"):
1. Título "Ingresa el código de verificación" (centrado, negrita)
2. Línea divisoria horizontal
3. Texto instructivo: "Hemos enviado un código de 6 dígitos a:"
4. Correo destacado en negrita: "usuario@municipalidad.cl"
5. **Fila de 6 casillas individuales** para dígitos del código, numeradas visualmente 1–6, cada una como un cuadro independiente
6. Texto pequeño: "El código expira en 10 minutos."
7. Botón primario ancho completo: "Verificar código"
8. Texto secundario centrado: "¿No recibiste el código?"
9. Enlace con temporizador: "Reenviar código (00:45)"
10. Enlace: "Volver al login"

---

## 4. Pantalla: Crear nueva contraseña

Contenida en ventana con barra decorativa superior (texto "Sistema Municipal - Nueva contraseña"):
1. Placeholder de imagen (logo)
2. Título "Sistema Municipal"
3. Subtítulo "Gestión de Atención Ciudadana"
4. Línea divisoria horizontal
5. Título de sección "Crea tu nueva contraseña"
6. Texto instructivo: "Tu nueva contraseña debe cumplir con los siguientes requisitos:"
7. **Lista de viñetas** (recuadro con fondo diferenciado), en orden:
   - Mínimo 8 caracteres
   - Al menos una letra mayúscula
   - Al menos una letra minúscula
   - Al menos un número
   - Al menos un carácter especial (ej: ! @ # $ %)
8. Campo "Nueva contraseña" con icono de candado a la izquierda + icono de "ojo" (mostrar/ocultar) a la derecha
9. Campo "Confirmar nueva contraseña" con icono de candado a la izquierda + icono de "ojo" a la derecha
10. Botón primario ancho completo: "Guardar contraseña"

---

## 5. Pantalla: Roles

Sigue el **patrón de vista "Listado"** (ver 0.4). Detalle específico:
- Título: "Roles"
- Botón de acción: "+ Nuevo Rol"
- Columnas de la tabla, en orden: `#` · `Nombre` · `Descripción` · `Acciones`
- Filas de ejemplo (contenido de referencia visual): Administrador / Operador / Consultor

---

## 6. Pantalla: Usuarios

Patrón "Listado". Detalle específico:
- Título: "Usuarios"
- Botón de acción: "+ Nuevo Usuario"
- Columnas, en orden: `#` · `Nombre` · `Correo` · `Rol` · `Estado` · `Acciones`
- La columna `Estado` usa texto de color semántico: verde/normal para "Activo", rojo para "Inactivo"

---

## 7. Pantalla: Delegaciones Municipales

Patrón "Listado". Detalle específico:
- Título: "Delegaciones Municipales"
- Botón de acción: "+ Nueva Delegación"
- Columnas, en orden: `#` · `Nombre` · `Dirección` · `Comuna` · `Acciones`

---

## 8. Pantalla: Metas (Items Metas)

Patrón "Listado". Detalle específico:
- Etiqueta de pantalla superior: "Items Metas"
- Título dentro del contenido: "Metas"
- Botón de acción: "+ Nueva Meta"
- Columnas, en orden: `#` · `Nombre` · `Descripción` · `Acciones`

---

## 9. Pantalla: Tipo de Atención

Patrón "Listado". Detalle específico:
- Título: "Tipo de Atención"
- Botón de acción: "+ Nuevo Tipo"
- Columnas, en orden: `#` · `Nombre` · `Descripción` · `Acciones`

---

## 10. Pantalla: Sub Atención

Patrón "Listado". Detalle específico:
- Título: "Sub Atención"
- Botón de acción: "+ Nueva Sub Atención"
- Columnas, en orden: `#` · `Nombre` · `Tipo de Atención` (columna de referencia/relación con la entidad "Tipo de Atención") · `Acciones`

---

## 11. Pantalla: Vecinos (CRUD)

Patrón "Listado", con variante de sidebar expandido (grupo "Mantenedores" abierto mostrando todos sus sub-ítems, incluyendo dos adicionales no vistos en otras capturas: "Atenciones" y "Tipo de Gestión", antes de "Vecinos"). Detalle específico:
- Etiqueta superior: "Vecinos / CRUD"
- Título dentro del contenido: "Vecinos"
- Subtítulo bajo el título: "CRUD de vecinos"
- Botón de acción: "+ Nuevo Vecino"
- Columnas, en orden: `#` · `Nombre` · `RUT` · `Dirección` · `Teléfono` · `Territorio` · `Tipo de Gestión` · `Estado` · `Acciones`
- La columna `Estado` usa el mismo tratamiento semántico de color visto en "Usuarios" (Activo / Inactivo)

---

## 12. Inventario consolidado de assets visuales

Elementos gráficos/iconográficos usados a lo largo del mockup (sin nombrar librerías):
- Placeholder de imagen tipo "montaña + sol" (logo genérico)
- Icono de persona (usuario / avatar)
- Icono de candado (contraseña)
- Icono de sobre (correo)
- Icono de lupa (buscar)
- Icono de "+" (agregar/nuevo)
- Icono de lápiz (editar)
- Icono de basurero (eliminar)
- Icono de ojo (mostrar/ocultar contraseña)
- Icono de casa (Inicio)
- Icono de personas/engranaje (Mantenedores)
- Icono de edificio (Delegaciones Municipales)
- Icono de gráfico de barras (Reportes)
- Chevron/flecha de expansión (▲▼) y de desplegable (▼)
- Círculos decorativos de barra de ventana (3 círculos tipo semáforo)
- Casillas individuales numeradas para código OTP (6 celdas)
- Etiquetas de estado con color semántico (verde = activo, rojo = inactivo)

## 13. Jerarquía tipográfica observada (orden de tamaño, sin nombrar fuente)
1. Título de marca / título de pantalla de autenticación (más grande, negrita)
2. Título de sección de listado (grande, negrita)
3. Subtítulo descriptivo (mediano, peso normal, color secundario/gris)
4. Texto de encabezado de tabla (pequeño, negrita, o mayúsculas)
5. Texto de celda de tabla (pequeño, peso normal)
6. Texto de ayuda / notas (más pequeño, color gris/atenuado)
