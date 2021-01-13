from django.db import models

# Create your models here.
class MailServer(models.Model):
    host = models.CharField(max_length=50)
    user = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    port = models.IntegerField()
    sender = models.CharField(max_length=50)

    def __str__(self):
      return "%s" % (self.host)

