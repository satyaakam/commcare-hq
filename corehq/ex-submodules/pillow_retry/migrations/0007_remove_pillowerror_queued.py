# Generated by Django 1.11.6 on 2017-11-10 09:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pillow_retry', '0006_auto_20170615_0327'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pillowerror',
            name='queued',
        ),
    ]
