README
старт работы
1)  скопируйте к себе на машину наш проект с github в папку /var/www/html(необходим работающий и настроенный сервер nginx или apache)
2) создайте базу данных  и пользователя  для сайта 
3)  запустите sql скрипт dump.sql применив его к вашей пустой базе данных (use *имя вашей базы данных*; в начале файла)
4) заполните фаил config.json
5)  установите все расширения для питона pip install -r requirements.txt
6) запустите start.py
7) запустите экземпляр сервера с помощбю команды 
 cd /var/www/html/memes && export FLASK_APP=main && sudo nohup python3 flask run --host=0.0.0.0  > log.txt 2>&1 &
8) сайт доступен по index.html в коре проекта - пример : copift.ru/memes/index.html
P.S также вы можете взять  пример файла создания сервиса для автоматического запуска flask  как сервиса из проекта (flask.service) для system.d
