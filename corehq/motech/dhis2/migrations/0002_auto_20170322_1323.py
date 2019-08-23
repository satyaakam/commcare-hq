# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-03-22 13:23

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dhis2', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jsonapilog',
            name='request_body',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='jsonapilog',
            name='request_error',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='jsonapilog',
            name='response_body',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='jsonapilog',
            name='response_status',
            field=models.IntegerField(null=True),
        ),
    ]
