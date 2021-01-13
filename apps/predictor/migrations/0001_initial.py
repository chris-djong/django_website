# Generated by Django 2.1.8 on 2020-12-09 18:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('stocks', '0004_auto_20201209_1947'),
    ]

    operations = [
        migrations.CreateModel(
            name='IndicatorHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('acc_dist', models.FloatField()),
                ('bollinger_upper', models.FloatField()),
                ('bollinger_lower', models.FloatField()),
                ('macd', models.FloatField()),
                ('macd_signal', models.FloatField()),
                ('stochastic', models.FloatField()),
                ('rsi', models.FloatField()),
                ('aroon_down', models.FloatField()),
                ('aroon_up', models.FloatField()),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stocks.Stock')),
            ],
        ),
    ]
