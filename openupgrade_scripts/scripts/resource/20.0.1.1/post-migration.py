# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def _name_flexible_calendars(env):
    """The flexible calendars created in pre-migration get a proper name"""
    calendars = (
        env["resource.calendar"]
        .with_context(active_test=False)
        .search([("name", "=", openupgrade.get_legacy_name("flexible"))])
    )
    calendars.write({"name": env._("Flexible hours")})


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env, "resource", "20.0.1.1/noupdate_changes.xml")
    _name_flexible_calendars(env)
