# Despliegue en AWS — Abstergo

Documenta los servicios y componentes en producción, la configuración y los
pasos de inicio o actualización. Los secretos no viven acá: van en el `.env`
del servidor, fuera del repositorio y de las evidencias públicas.

## 1. Servicios y componentes

| Componente | Rol en el sistema |
|---|---|
| EC2 (Amazon Linux) | Instancia que hospeda la aplicación |
| Apache (`httpd`) | Servidor frontal: sirve `/static/` y hace `ProxyPass /` a gunicorn |
| gunicorn | Servidor WSGI de Django, escucha en `127.0.0.1:8000` |
| systemd (`abstergo.service`) | Mantiene gunicorn corriendo y lo reinicia |
| MariaDB | Base de datos relacional del sistema |
| Repositorio Git (GitHub) | Fuente del código; `main` es la rama de entrega |

## 2. Configuración

- Host: `18.209.251.129` · usuario `ec2-user` · llave `~/.ssh/abstergo-key.pem`.
- Proyecto: `/home/ec2-user/abstergo`; entorno virtual en `.../venv`.
- Estáticos: `collectstatic` escribe en `~/abstergo/staticfiles` y Apache sirve
  desde `/var/www/abstergo-static/`. Por eso, al cambiar estáticos, hay que
  copiar de uno al otro (ver paso 3).
- Variables de entorno en `~/abstergo/.env`: `SECRET_KEY`, `DEBUG=False`,
  `ALLOWED_HOSTS`, credenciales de MariaDB, correo y `OTP_*`.

## 3. Actualización (pasos)

```bash
ssh -i ~/.ssh/abstergo-key.pem ec2-user@18.209.251.129 '
cd ~/abstergo && \
git pull --ff-only origin main && \
~/abstergo/venv/bin/pip install -q -r requirements.txt && \
~/abstergo/venv/bin/python manage.py check && \
~/abstergo/venv/bin/python manage.py migrate --noinput && \
~/abstergo/venv/bin/python manage.py cargar_datos && \
~/abstergo/venv/bin/python manage.py collectstatic --noinput && \
sudo -n cp -a ~/abstergo/staticfiles/. /var/www/abstergo-static/ && \
sudo -n systemctl restart abstergo && \
echo DESPLEGADO
'
```

El `cp` a `/var/www/abstergo-static/` es obligatorio cuando cambian estáticos:
`collectstatic` no escribe ahí directamente.

## 4. Verificación en vivo

```bash
for u in /login/ /privacidad/ /api/docs/ /static/js/atencion.js; do
  printf "%-28s -> %s\n" "$u" \
    "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 http://18.209.251.129$u)"
done
```

Se espera `200` en todos. Las rutas protegidas dan `302` sin sesión.

## 5. Datos y secretos

- Los datos son ficticios y se regeneran con `python manage.py cargar_datos`
  (idempotente) desde `datos_nuevos/`.
- El `.env` no se versiona (`.gitignore`). El ejemplo sin secretos es
  `.env.example`.
- No se incluyen contraseñas, tokens ni claves en las evidencias.

## 6. Acceso de evaluación

- URL: `http://18.209.251.129` (o el dominio acordado con el docente).
- Cuentas de prueba: por rol (admin, coordinador, delegado, funcionario,
  verificador, consulta), cargadas por `cargar_datos`. La clave inicial se
  define en `USUARIOS_PASSWORD_INICIAL` del `.env`.
