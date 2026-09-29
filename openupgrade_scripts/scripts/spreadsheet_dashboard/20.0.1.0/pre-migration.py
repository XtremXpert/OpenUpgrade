# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # the name of a share was related to the dashboard, it is stored and
    # required now
    openupgrade.add_fields(
        env,
        [
            (
                "name",
                "spreadsheet.dashboard.share",
                "spreadsheet_dashboard_share",
                "char",
                False,
                "spreadsheet_dashboard",
            )
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE spreadsheet_dashboard_share share
        SET name = COALESCE(dashboard.name->>'en_US', 'Dashboard')
        FROM spreadsheet_dashboard dashboard
        WHERE dashboard.id = share.dashboard_id AND share.name IS NULL
        """,
    )
