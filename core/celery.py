from __future__ import absolute_import

import os
import django
# This is omehow needed in order to overwrite the varible settings
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
from django.conf import settings
redis_host = settings.REDIS_HOST
from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

app = Celery("stocki", 
        broker="redis://" + settings.REDIS_HOST + ":6379",
        backend="redis://" + settings.REDIS_HOST + ":6379") 

app.conf.update(
  timezone="Europe/Amsterdam",
  CELERY_TASK_SERIALIZER="json",
  CELERY_RESULT_SERIALIZER="json"
  
  )


# Use django project file as settings file 
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


if __name__ == '__main__': 
    app.start()
