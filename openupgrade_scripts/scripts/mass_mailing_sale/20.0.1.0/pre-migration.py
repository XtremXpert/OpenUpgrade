# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        """
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'mailing_mailing' AND column_name = 'sale_invoiced_amount'
        """
    )
    row = env.cr.fetchone()
    if row and row[0] == "integer":
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE mailing_mailing
                ALTER COLUMN sale_invoiced_amount TYPE double precision
            """,
        )
