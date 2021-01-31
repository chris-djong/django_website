# Generated by Django 3.1.5 on 2021-01-31 10:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('stocks', '0009_stock_iexfinance_ticker'),
    ]

    operations = [
        migrations.CreateModel(
            name='IexApiKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sandbox', models.BooleanField(unique=True)),
                ('token', models.CharField(max_length=50)),
                ('messages_available', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='KeyStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('avg10Volume', models.IntegerField()),
                ('avg30Volume', models.IntegerField()),
                ('day200MovingAvg', models.FloatField()),
                ('day30ChangePercent', models.FloatField()),
                ('day50MovingAvg', models.FloatField()),
                ('day5ChangePercent', models.FloatField()),
                ('dividendYield', models.FloatField()),
                ('employees', models.IntegerField()),
                ('exDividendDate', models.DateField()),
                ('marketcap', models.FloatField()),
                ('maxChangePercent', models.FloatField()),
                ('month1ChangePercent', models.FloatField()),
                ('month3ChangePercent', models.FloatField()),
                ('month6ChangePercent', models.FloatField()),
                ('nextDividendDate', models.DateField()),
                ('nextEarningsDate', models.DateField()),
                ('peRatio', models.FloatField()),
                ('sharesOutstanding', models.IntegerField()),
                ('ttmDividendRate', models.FloatField()),
                ('ttmEPS', models.FloatField()),
                ('week52change', models.FloatField()),
                ('week52high', models.FloatField()),
                ('week52low', models.FloatField()),
                ('year1ChangePercent', models.FloatField()),
                ('year2ChangePercent', models.FloatField()),
                ('year5ChangePercent', models.FloatField()),
                ('ytdChangePercent', models.FloatField()),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stocks.stock')),
            ],
        ),
        migrations.CreateModel(
            name='BalanceSheet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('commonStock', models.IntegerField()),
                ('currentAssets', models.FloatField()),
                ('currentCash', models.FloatField()),
                ('fiscalDate', models.DateField()),
                ('fiscalQuarter', models.IntegerField()),
                ('fiscalYear', models.IntegerField()),
                ('goodwill', models.FloatField()),
                ('intangibleAssets', models.FloatField()),
                ('inventory', models.FloatField()),
                ('longTermDebt', models.FloatField()),
                ('longTermInvestments', models.FloatField()),
                ('minorityInterest', models.FloatField()),
                ('netTangibleAssets', models.FloatField()),
                ('otherAssets', models.FloatField()),
                ('otherCurrentAssets', models.FloatField()),
                ('propertyPlantEquipment', models.FloatField()),
                ('receivables', models.FloatField()),
                ('reportDate', models.FloatField()),
                ('retainedEarnings', models.FloatField()),
                ('shareholderEquity', models.FloatField()),
                ('totalAssets', models.FloatField()),
                ('totalCurrentLiabilities', models.FloatField()),
                ('totalLiabilities', models.FloatField()),
                ('treasuryStock', models.FloatField()),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stocks.stock')),
            ],
        ),
    ]
