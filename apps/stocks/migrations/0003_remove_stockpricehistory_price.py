# Generated by Django 2.1.8 on 2020-12-08 20:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0002_stockpricehistory_v'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stockpricehistory',
            name='price',
        ),
    ]
