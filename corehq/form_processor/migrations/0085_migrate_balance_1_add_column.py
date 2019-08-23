# -*- coding: utf-8 -*-

from django.db import migrations

from corehq.sql_db.operations import RawSQLMigration


migrator = RawSQLMigration(('corehq', 'form_processor', 'migrations', 'sql_templates'))


class Migration(migrations.Migration):

    dependencies = [
        ('form_processor', '0084_migrate_delta_5_alter_field'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrator.get_migration('migrate_balance_1_add_column.sql'),
            ]
        ),
    ]
