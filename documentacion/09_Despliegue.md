# 09 · Despliegue en EC2 (Amazon Linux 2023)

Desde SSH, como `ec2-user`. Reemplazar `CLAVE`, `<dominio>` y el SMTP.

## 1. Paquetes
```bash
sudo dnf install -y mariadb105-server mariadb105-devel gcc python3-devel httpd
sudo systemctl enable --now mariadb
```

## 2. Base de datos
```bash
sudo mariadb -e "CREATE DATABASE abstergo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mariadb -e "CREATE USER 'abstergo'@'localhost' IDENTIFIED BY 'CLAVE'; GRANT ALL PRIVILEGES ON abstergo.* TO 'abstergo'@'localhost'; FLUSH PRIVILEGES;"
```

## 3. Código y dependencias
```bash
cd ~ && git clone https://github.com/lacteada/abstergo.git && cd abstergo
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install mysqlclient        # necesita los headers de MariaDB (paso 1)
```

## 4. Variables de entorno
```bash
cp .env.example .env && nano .env
```
Dejar `DEBUG=False`, `ALLOWED_HOSTS=<dominio>`, `DB_PASSWORD`, y el SMTP.

## 5. Django
```bash
python manage.py migrate
python manage.py cargar_datos
python manage.py collectstatic --noinput
```

## 6. gunicorn como servicio
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

## 7. Apache (proxy + estáticos)
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

## 8. Security Group
Abrir HTTP (80) desde tu IP.

## 9. Verificar
- `http://<dominio>/` abre el login.
- `sudo journalctl -u abstergo -f`.

## 10. phpMyAdmin (opcional)
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

## Notas
- El orden en Apache importa: `/static/` y `/phpmyadmin` van antes del `ProxyPass /`.
- `.env` nunca se versiona.
- Si agregás HTTPS, sumá `CSRF_TRUSTED_ORIGINS=https://tu-dominio` al `.env`.
