@echo off
REM Riavvia RabbitMQ Server
net stop RabbitMQ
net start RabbitMQ

REM Avvia Celery worker
start "" cmd /c "celery -A gestione_palestra worker --pool=solo"


REM Esegui le migrazioni e avvia il server Django
python manage.py makemigrations gestione_palestra management palestra
python manage.py migrate
python manage.py migrate --run-syncdb
python manage.py runserver


