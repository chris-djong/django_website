# Generated by Django 3.1.5 on 2021-01-24 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0005_auto_20210114_2249'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='portfolio',
            field=models.IntegerField(default=0),
        ),
    ]
