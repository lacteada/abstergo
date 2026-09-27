### Steps followed

- Setup AWS and Git
    - `.gitignore` en la raíz del repositorio (excluye venv, .env, *.pem, cachés)
    - Llave SSH en `~/.ssh/abstergo-key.pem`, fuera del repositorio
    - Amazon Linux 2023 (kernel-6.18)
    - `ssh -i "abstergo-key.pem" ec2-user@ec2-54-172-183-44.compute-1.amazonaws.com`
    - `sudo dnf upgrade -y`
    - `sudo dnf install -y httpd wget php-fpm php-mysqli php-json php php-devel python3`
    - `sudo dnf install mariadb105-server`
    - https://docs.aws.amazon.com/linux/al2023/ug/ec2-lamp-amazon-linux-2023.html#prepare-lamp-server-2023
- venv
    - `python -m venv venv`
    - `source venv/bin/activate`
    - `python -m pip install Django`