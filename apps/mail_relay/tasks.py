import smtplib
from email.mime.text import MIMEText
from .models import MailServer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from core.celery import app


# This function send a mail from sender to targets [target1, target2] with subject and message 
@app.task()
def send_mail(sender, targets, subject, message):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(targets)

    server_data = MailServer.objects.filter(host = "mail.dejong.lu")[0]
    server = smtplib.SMTP_SSL(server_data.host, server_data.port)
    server.login(server_data.user, server_data.password)
    server.sendmail(sender, targets, msg.as_string())
    server.quit()

