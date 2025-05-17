import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'davtj_web.settings')
app = Celery('davtj_web')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()