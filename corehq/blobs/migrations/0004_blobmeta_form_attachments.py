# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-26 15:11

from django.db import migrations

from corehq.sql_db.operations import RawSQLMigration
from corehq.sql_db.migrations import partitioned

migrator = RawSQLMigration(('corehq', 'blobs', 'sql_templates'), {})


@partitioned
class Migration(migrations.Migration):

    dependencies = [
        ('blobs', '0003_big_content'),
    ]

    operations = [
        # this was accidentally removed by 0003_big_content
        # drop first in case it already exists
        migrations.RunSQL(
            """
            ALTER TABLE blobs_blobmeta DROP CONSTRAINT IF EXISTS
                blobs_blobmeta_content_length_check;
            ALTER TABLE blobs_blobmeta ADD CONSTRAINT
                blobs_blobmeta_content_length_check CHECK (content_length >= 0);
            """,
            "SELECT 1"
        ),

        partitioned(migrator.get_migration('get_blobmetas.sql'), apply_to_proxy=False),
        migrator.get_migration('setup_blobmeta_view.sql', 'drop_blobmeta_view.sql'),
        migrator.get_migration('restrict_legacy_attachment_metadata_insert.sql', testing_only=True),
    ]
