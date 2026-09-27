# Normas Gráficas — Ilustre Municipalidad de La Serena

Referencia de identidad visual oficial para el sistema.

- **Fuente:** `https://laserena.cl/conocenos/normas-graficas`
- **Contenido:** servido por la API del portal (`apis.munilaserena.cl/api-portal`, ítem "Normas Gráficas" del menú "Conócenos").
- **Manual citado por la propia página:** normas de 2019.
- **Recuperado:** 2026-09-24.

---

## 1. Logotipo institucional (HERÁLDICO)

Cuatro variantes, cada una en SVG y PNG:

- **Horizontal blanco** — `https://framework.laserena.cl/img/horizontal-blanco.svg` · `.png`
- **Horizontal color** — `https://framework.laserena.cl/img/horizontal-color.svg` · `.png`
- **Vertical blanco** — `https://framework.laserena.cl/img/vertical-blanco.svg` · `.png`
- **Vertical color** — `https://framework.laserena.cl/img/vertical-color.svg` · `.png`

Verificado: los ocho archivos responden 200.

## 2. Aplicación del logotipo

- La página muestra cada variante sobre tres fondos para demostrar su uso correcto: fondo institucional rojo, fondo blanco y fondo oscuro.
- El logotipo blanco se usa sobre rojo institucional y sobre negro; el logotipo a color se usa sobre blanco.
- Cada variante tiene botones de descarga directa en SVG y PNG.

## 3. El emblema

- Se trabajó respetando su esencia y estructura original, **sin** sintetizarlo ni reducirlo.
- Solo se hicieron ajustes mínimos para asegurar su reproducción en distintos formatos y tamaños.
- El objetivo declarado es mantener intacta su carga simbólica e histórica y su carácter solemne.

## 4. Colores institucionales

Rojo Luminoso
- HEX `#DB3334`
- RGB 219, 51, 52
- CMYK 7, 91, 79, 1
- Pantone 200 C

Rojo Heráldico
- HEX `#C41230`
- RGB 196, 18, 48
- CMYK 0, 100, 63, 12
- Pantone 200 C

Rojo Oscuro
- HEX `#8B1D19`
- RGB 139, 29, 25
- CMYK 28, 98, 94, 33
- Pantone 200 C

Complementos y jerarquía
- Negro profundo para sobriedad y formalidad.
- Gris oscuro como neutro de apoyo.
- Las tres rojos comparten Pantone 200 C, lo que refleja que son variaciones de un mismo rojo y no colores distintos.
- **Recomendación explícita de la página:** usar el **Rojo Heráldico `#C41230` como color principal**.

## 5. Notas para el proyecto

- El manual (2019) fija `#C41230` como color principal, pero el portal real **no lo aplica**: su CSS usa `#AD0000` y su `theme-color` usa `#920000`.
- Es decir, el sitio en producción es inconsistente con su propio manual. Para el sistema conviene elegir una referencia y sostenerla.
- Propuesta de tokens, derivada del manual (no está en la fuente):
  - Principal: `#C41230` (Rojo Heráldico).
  - Énfasis claro: `#DB3334` (Rojo Luminoso).
  - Oscuro / hover: `#8B1D19` (Rojo Oscuro).
  - Superficies oscuras: negro profundo y gris oscuro de apoyo.
- El manual no define tipografía, espaciados ni componentes: solo logotipo y color. Esos aspectos hay que definirlos aparte.
