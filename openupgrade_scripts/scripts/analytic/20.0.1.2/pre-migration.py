# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # analytic_distribution is required now
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_analytic_distribution_model
        SET analytic_distribution = '{}'::jsonb
        WHERE analytic_distribution IS NULL
        """,
    )
