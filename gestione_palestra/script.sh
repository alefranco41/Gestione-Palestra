sudo service rabbitmq-server restart; python3 manage.py makemigrations gestione_palestra management palestra && python3 manage.py migrate && python3 manage.py migrate --run-syncdb && python3 manage.py runserver & celery -A gestione_palestra worker --beat
