import smtplib
from email.mime.text import MIMEText
from .models import MailServer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .tasks import send_mail


# Send an alert mail to the user of stock that the given stock has passed the alert mail 
# in case upper is true then the upper alert has been reached and lower alert otherwise
def send_alert_mail(transaction, upper):
    user = get_object_or_404(User, username=transaction.user)
    if user.email == "":
        return
    targets = [user.email]
    sender = "finance@dejong.lu"
    if upper:
        subject = "Climbing alert for %s" % transaction.stock.ticker
        message = "Hello %s\n\n This is an automatic alert for your %s stock.\n\n Your stock is climbing. The current price is given by %f, you have set an alert to %f\n\nYour alert has been removed from the transaction.\n\n" % (user.username, transaction.stock.ticker, round(transaction.stock.price_today, 2), round(transaction.upper_alert, 2))
    else:
        subject = "Falling alert for %s" % transaction.stock.ticker
        message = "Hello %s\n\n This is an automatic alert for your %s stock.\n\n Your stock is falling. The current price is given by %f, you have set an alert to %f\n\nYour alert has been removed from the transaction.\n\n" % (user.username, transaction.stock.ticker, round(transaction.stock.price_today, 2), round(transaction.lower_alert, 2))
    send_mail(sender, targets, subject, message)
