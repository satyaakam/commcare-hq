# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-08-20 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userreports', '0015_auto_20190701_2006'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asyncindicator',
            name='id',
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]
