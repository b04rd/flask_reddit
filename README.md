Инструкция по развертыванию борды
=================================

Этот проект поддерживается на данный момент командой [борды mipt.me](http://mipt.me). Любая помощь (багрепорты, перевод, дизайн, написание кода) горячо приветствуется. Если (вдруг) вы захотели пожертвовать деньги на развитие [борды](http://mipt.me), то пишите текущим разработчикам.

Этот проект -- форк [flask_reddit](https://github.com/codelucas/flask_reddit) от Lucas Ou-Yang.

Установка
---------

Протестирована на Ubuntu 14.04 LTS и Debian 8 Jessie. В качестве веб-сервера используется nginx, WSGI-сервер -- Gunicorn, СУБД -- MySQL. Приложение будет расположено в `/opt/board`, отдельный юзер для запуска борды `board`.

0.  Настраиваем iptables по вкусу. Рекомендуемая схема: дефолтная политика DROP для внешних интерфейсов, открыть наружу порты 22 (SSH), 80 (HTTP) или 443 (HTTPS), установка правил на загрузке при помощи `iptables-persistent` (прописать правила в /etc/iptables/rules.v4, перезапустить с помощью `sudo service netfilter-persistent restart`).

1.  Установливаем с помощью пакетного менеджера git, MySQL, nginx, supervisor и
virtualenv для питона:

        $ sudo apt-get install git mysql-server libmysqlclient-dev nginx supervisor python-virtualenv python-dev

    При установке `mysql-server` требуется ввести пароль для пользователя root в БД. **Не забываем этот пароль!**

2.  Создаем пользователя для борды и клонируем репозиторий:

        $ sudo useradd -d /opt/board -M -r -s /bin/false board
        $ sudo mkdir /opt/board
        $ sudo chown ${USER}:board /opt/board
        $ git clone --depth=1 https://github.com/b04rd/flask_reddit.git /opt/board

3.  Настраиваем MySQL: пишем конфиг.

    В файле `/etc/mysql/my.cnf` добавляем следующие опции в соответствующие разделы:

        [client]
        default-character-set = utf8

        [mysqld]
        character-set-server = utf8
        collation-server = utf8mb4_general_ci
        init-connect = 'SET NAMES utf8'

    Также проверяем, что следующие опции выставлены именно так (с точностью до порядка):

        [mysqld]
        bind-address = 127.0.0.1
        port = 3306
        user = mysql

    Перезапускаем MySQL (например, `sudo service mysql restart`).

    Опционально: проверяем, что всё влетело. Если всё нормально, то вывод должен соответствовать приведенному.

        $ sudo service mysql restart
        $ mysql -u root -p
        [вводим пароль для БД]
        mysql> SHOW VARIABLES WHERE Variable_name LIKE 'character\_set\_%' OR Variable_name LIKE 'collation%';
        +--------------------------+--------------------+
        | Variable_name            | Value              |
        +--------------------------+--------------------+
        | character_set_client     | utf8               |
        | character_set_connection | utf8               |
        | character_set_database   | utf8               |
        | character_set_filesystem | binary             |
        | character_set_results    | utf8               |
        | character_set_server     | utf8               |
        | character_set_system     | utf8               |
        | collation_connection     | utf8_general_ci    |
        | collation_database       | utf8_general_ci    |
        | collation_server         | utf8_general_ci    |
        +--------------------------+--------------------+
        10 rows in set (0.00 sec)

4.  Настраиваем MySQL - 2: создаем базу данных и юзера для борды. Входим в консольный клиент БД с помощью `mysql -u root -p`, вводя пароль для **рута в БД** (выйти можно, нажав Ctrl-D). После чего, следующими командами создаем базу данных и юзера для борды. `password` следует заменить на реальный пароль для бордового юзера.

        CREATE DATABASE board;
        CREATE USER 'board'@'localhost' IDENTIFIED BY 'password';
        GRANT CREATE,DROP,DELETE,INSERT,SELECT,UPDATE ON board.* TO 'board'@'localhost';
        FLUSH PRIVILEGES;

5.  Устанавливаем в virtualenv зависимости.

        $ cd /opt/board
        $ virtualenv venv
        $ source venv/bin/activate    # активируем ("входим в") virtualenv
        (venv)$ pip install -r requirements.txt   # выйти из virtualenv можно, набрав deactivate

6.  Настраиваем приложение.

    Как образец можно использовать `app_config.py` в корне проекта.

    Абсолютно необходимо в опции `SECRET_KEY` указать достаточно длинную случайную последовательность из символов. Сгенерировать ее можно, например, так (в GNU/Linux):

        $ dd if=/dev/urandom bs=64 count=1 2>/dev/null | base64 -w0

    Также следует установить `DOMAIN` и `ROOT_URL` в нужные значения, `STATIC_ROOT` -- в `"/opt/board/flask_reddit/static"`, в `SQLALCHEMY_DATABASE_URI` указать тип СУБД, юзера, пароль и имя БД, например, `"mysql://board:password@localhost/board"`. Ключи для рекапчи можно получить, зарегавшись на соответствующей странице в Google.

    **NB!** Готовый конфиг должен называться `config.py` и лежать в корне проекта!

7.  Настраиваем supervisor и gunicorn.

    Gunicorn настраивать, как таковой, не надо, нужный конфиг уже есть в дереве.

    Для supervisor можно также использовать готовый конфиг в корне проекта (`supervisor.conf`), который необходимо скопировать в `/etc/supervisor/conf.d/board.conf`.

    С данными настройками веб-приложение будет работать по адресу localhost:8040. Чтобы вывести его наружу (и, возможно, держать несколько сайтов), необходим прокси в виде nginx.

8.  Настраиваем виртуальный хост в nginx.

    Создаем файл `/etc/nginx/sites-available/board` со следующим содержимым(`SERVER_DOMAIN` заменяем на домен сайта):

    ```
    server {
        listen 80;
        server_name SERVER_DOMAIN;

        location /static/ {
            alias /opt/board/flask_reddit/static/;
            expires max;
        }

        location / {
            proxy_pass http://localhost:8040;
            proxy_set_header X-Forwarded-Host $server_name;
            proxy_set_header X-Real-IP $remote_addr;
            add_header P3P 'CP="ALL DSP COR PSAa PSDa OUR NOR ONL UNI COM NAV"';
        }
    }
    ```

    После этого ставим симлинк на этот файл в `/etc/nginx/sites-enabled` и удаляем оттуда симлинк на default. Перезапускаем nginx.

9.  Запускаем приложение.

    Делаем начальные установки, запустив `python2.7 kickstart.py`, находясь в /opt/board в virtualenv. Перед этим можно поменять в этом скрипте э-почту рут-пользователя, его пароль и параметры основного субреддита.

    Создаем директорию для логов приложения и запускаем его:

        $ sudo mkdir /var/log/board
        $ sudo chown board:board /var/log/board
        $ sudo chmod 755 /var/log/board
        $ sudo service supervisor restart
        $ sudo supervisorctl status board

    Если последняя команда дала вывод вроде

        board                            RUNNING    pid 3534, uptime 0:00:27

    то приложение запустилось успешно.

10. Добавляем в крон регулярные задания.

    Добавляем в кронтаб для юзера board следующую строку:

        */1 * * * * PYTHONPATH=/opt/board:/opt/board/venv /opt/board/venv/bin/python /opt/board/scripts/set_hotness_all.py >> /var/log/board/set_hotness_all.log 2>&1

    **NB!** Кронтаб нужно редактировать ТОЛЬКО с помощью команды `sudo crontab -u board -e`!


Управление приложением
----------------------

Запуск/остановку приложения можно проводить с помощью команд `sudo supervisorctl start board` и `sudo supervisorctl stop board`.

Логи приложения лежат в `/var/log/board/`, логи веб-сервера в `/var/log/nginx`.


Некоторые соображения
---------------------

- При желании можно заменить supervisor на upstart-овый сервис или systemd-шный юнит.
- Возможно, надежнее использовать LXC-контейнеры вместо virtualenv.
- Похоже, что возможно вместо MySQL использовать MariaDB или PostgreSQL. Но такая конфигурация не тестировалась.
