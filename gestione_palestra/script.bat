@echo off
REM Riavvia RabbitMQ Server
net stop RabbitMQ
net start RabbitMQ

REM Attiva l'ambiente virtuale
call <virtual_env_name>\Scripts\activate

REM Esegui le migrazioni e avvia il server Django
python manage.py makemigrations gestione_palestra management palestra
python manage.py migrate
python manage.py migrate --run-syncdb
start python manage.py runserver

REM Avvia Celery worker
start celery -A gestione_palestra worker --beat
