# 09 · Despliegue en EC2 (Amazon Linux 2023)

Desde SSH, como `ec2-user`. Reemplazar `CLAVE`, `<dominio>` y el SMTP.

**Dos versiones mínimas**
Django 6.1 exige **Python 3.12** y **MariaDB 10.11**. Amazon Linux 2023 trae Python 3.9 como `python3` y MariaDB 10.5 en sus repositorios, así que ninguno de los dos sirve tal cual y hay que traerlos aparte.

## 1. Paquetes del sistema
```bash
sudo dnf install -y gcc python3.12 python3.12-devel httpd
```
`python3.12-devel` y no `python3-devel`: el segundo es para 3.9 y `mysqlclient` no compila contra él.

## 2. MariaDB 11.4 desde el repositorio oficial
El repositorio de Amazon Linux 2023 solo tiene MariaDB 10.5, y Django la rechaza. Se agrega el repositorio oficial de MariaDB, forzando RHEL 9, porque su script de instalación no reconoce Amazon Linux:

```bash
sudo curl -sSLo /etc/pki/rpm-gpg/MariaDB-Server-GPG-KEY https://supplychain.mariadb.com/MariaDB-Server-GPG-KEY
sudo rpm --import /etc/pki/rpm-gpg/MariaDB-Server-GPG-KEY

sudo tee /etc/yum.repos.d/mariadb.repo >/dev/null <<'EOF'
[mariadb-main]
name = MariaDB Server
baseurl = https://dlm.mariadb.com/repo/mariadb-server/11.4/yum/rhel/9/x86_64
gpgkey = file:///etc/pki/rpm-gpg/MariaDB-Server-GPG-KEY
gpgcheck = 1
enabled = 1
module_hotfixes = 1
EOF

sudo dnf clean all
sudo dnf repolist | grep -i mariadb
sudo dnf install -y MariaDB-server MariaDB-client MariaDB-devel MariaDB-shared
sudo systemctl enable --now mariadb
sudo mariadb -e "SELECT VERSION();"
```

Verificado: esa `baseurl` responde y resuelve a MariaDB 11.4.13, y los cuatro paquetes existen con ese nombre. Los RPM son de RHEL 9 y Amazon Linux 2023 es compatible a nivel de binarios, pero no es una combinación oficialmente soportada.

`SELECT VERSION()` tiene que decir 11.4.x. Si dice 10.5, quedó un paquete `mariadb105` instalado y hay que quitarlo antes.

## 3. Base de datos y usuario
```bash
sudo mariadb -e "CREATE DATABASE abstergo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mariadb -e "CREATE USER 'abstergo'@'localhost' IDENTIFIED BY 'CLAVE'; GRANT ALL PRIVILEGES ON abstergo.* TO 'abstergo'@'localhost'; FLUSH PRIVILEGES;"
```
`CLAVE` tiene que ser la misma que `DB_PASSWORD` del `.env`.

## 4. Código y dependencias
```bash
cd ~ && git clone https://github.com/lacteada/abstergo.git && cd abstergo
/usr/bin/python3.12 -m venv venv
source venv/bin/activate
python -V
pip install -r requirements.txt
pip install mysqlclient
```
`python -V` tiene que decir 3.12.x antes de instalar nada. No sirve `python3 -m venv`: en Amazon Linux 2023 `python3` es 3.9, y un venv creado así queda apuntando al intérprete equivocado.

Si el venv quedó mezclado de un intento anterior, se rehace desde cero: `rm -rf venv` y repetir el bloque.

## 5. Variables de entorno
```bash
cp .env.example .env && nano .env
```
Dejar así:

```bash
SECRET_KEY=<cadena larga y aleatoria>
DEBUG=False
ALLOWED_HOSTS=<dominio-o-ip>
DB_NAME=abstergo
DB_USER=abstergo
DB_PASSWORD=<la misma del paso 3>
DB_HOST=127.0.0.1
DB_PORT=3306

MAILER_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=<SMTP login de Brevo>
EMAIL_HOST_PASSWORD=<SMTP key de Brevo>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=<correo remitente verificado>

USUARIOS_PASSWORD_INICIAL=<contraseña para los usuarios migrados>
```

- `SECRET_KEY` llega vacía en el `.env.example`, y sin valor Django levanta un 500 en todas las páginas. Se genera con `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- Puerto 587 y no 465: el bloque `MAILERS` de `settings.py` solo pasa `use_tls`.
- `USUARIOS_PASSWORD_INICIAL` sin valor deja a los usuarios migrados con contraseña vacía.

## 6. Django
```bash
python manage.py showmigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py cargar_datos
python manage.py collectstatic --noinput
```

- `showmigrations` va primero. Si aparece `[X]` en los `0001_initial` y la base venía de un esquema anterior, hay que recrearla antes de migrar: `migrate` no va a rehacer esas tablas porque las considera aplicadas.
- `createsuperuser` pide **correo**, no nombre de usuario.
- `cargar_datos` es reejecutable: la segunda corrida informa `0 creados`.
- Recargar el JSON restaura las filas dadas de baja, porque el comando usa el gestor sin filtro y limpia la fecha.

## 7. gunicorn como servicio
```bash
sudo tee /etc/systemd/system/abstergo.service >/dev/null <<EOF
[Unit]
Description=abstergo
After=network.target mariadb.service

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/abstergo
ExecStart=/home/ec2-user/abstergo/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now abstergo
```

## 8. Apache (proxy + estáticos)
```bash
sudo mkdir -p /var/www/abstergo-static
sudo cp -r ~/abstergo/staticfiles/* /var/www/abstergo-static/
sudo tee /etc/httpd/conf.d/abstergo.conf >/dev/null <<'EOF'
ProxyPreserveHost On
Alias /static/ /var/www/abstergo-static/
ProxyPass /static/ !
ProxyPass / http://127.0.0.1:8000/
ProxyPassReverse / http://127.0.0.1:8000/
EOF
sudo setsebool -P httpd_can_network_connect 1
sudo systemctl enable --now httpd && sudo systemctl restart httpd
```
Tras cada `collectstatic`, repetir el `cp`.

## 9. Security Group
Abrir HTTP (80) desde tu IP.

## 10. Verificar
- `http://<dominio>/` abre el login.
- El login es por correo. Un usuario sin correo no entra: existe, pero su contraseña es inutilizable.
- `/recuperar/` manda el código por correo y `/validar/` lo pide.
- `sudo journalctl -u abstergo -f`.

## 11. phpMyAdmin (opcional)
```bash
sudo dnf install -y php php-mysqli php-mbstring php-xml
cd /var/www/html
sudo wget https://www.phpmyadmin.net/downloads/phpMyAdmin-latest-all-languages.tar.gz
sudo mkdir phpMyAdmin && sudo tar -xzf phpMyAdmin-latest-all-languages.tar.gz -C phpMyAdmin --strip-components=1
sudo rm phpMyAdmin-latest-all-languages.tar.gz
sudo tee /etc/httpd/conf.d/phpmyadmin.conf >/dev/null <<'EOF'
Alias /phpmyadmin /var/www/html/phpMyAdmin
<Directory /var/www/html/phpMyAdmin>
  Require ip TU_IP_PUBLICA
</Directory>
EOF
sudo systemctl restart httpd
```

## 12. Actualizar un despliegue que ya existe
```bash
cd ~/abstergo && source venv/bin/activate
git pull origin main
python manage.py showmigrations      # ¿la base quedó del esquema anterior?
python manage.py migrate
python manage.py cargar_datos
python manage.py collectstatic --noinput
sudo cp -r ~/abstergo/staticfiles/* /var/www/abstergo-static/
sudo systemctl restart abstergo
```
No hace falta `pip install` si `requirements.txt` no cambió. El `.env` no llega con el `pull`: está en `.gitignore`, así que el de la instancia se conserva y hay que editarlo a mano cuando cambie algo.

## Notas
- El orden en Apache importa: `/static/` y `/phpmyadmin` van antes del `ProxyPass /`.
- `.env` nunca se versiona.
- Si agregás HTTPS, sumá `CSRF_TRUSTED_ORIGINS=https://tu-dominio` al `.env`.
- El venv tiene que ser de Python 3.12 y la base de MariaDB 11.4. Las dos cosas son requisitos de Django 6.1, no preferencias.
