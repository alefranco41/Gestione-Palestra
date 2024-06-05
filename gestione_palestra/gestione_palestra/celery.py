# In un file celery.py nella tua cartella del progetto
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Imposta il modulo Django predefinito per Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestione_palestra.settings')

# Crea un'istanza di Celery
app = Celery('gestione_palestra')

# Carica le impostazioni di configurazione di Celery dal file settings.py del tuo progetto
app.config_from_object('django.conf:settings', namespace='CELERY')

# Ricerca automaticamente task in un modulo tasks.py all'interno delle tue app Django
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
