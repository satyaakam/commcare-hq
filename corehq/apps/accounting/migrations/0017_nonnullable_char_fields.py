# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-03-13 17:56

from django.db import migrations




def _assign_default_values(apps, schema_editor):
    Subscription = apps.get_model('accounting', 'Subscription')
    Subscription.objects.filter(
        no_invoice_reason__isnull=True
    ).update(no_invoice_reason='')
    Subscription.objects.filter(
        salesforce_contract_id__isnull=True
    ).update(salesforce_contract_id='')


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0016_grandfather_reportbuilder_5_pro'),
    ]

    operations = [
        migrations.RunPython(_assign_default_values),
    ]
