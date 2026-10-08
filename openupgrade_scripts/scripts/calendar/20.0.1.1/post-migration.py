# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def _default_privacy(cr):
    """The default privacy of a user (res.users.settings) is now the default
    privacy of their primary calendar, created by the ORM when computing
    calendar_id on the events."""
    if not openupgrade.column_exists(
        cr, "res_users_settings", "calendar_default_privacy"
    ):
        return
    openupgrade.logged_query(
        cr,
        """
        UPDATE calendar_calendar calendar
        SET calendar_default_privacy = settings.calendar_default_privacy
        FROM calendar_user calendar_user
        JOIN res_users_settings settings ON settings.user_id = calendar_user.user_id
        WHERE calendar_user.calendar_id = calendar.id
            AND calendar_user.is_primary
            AND settings.calendar_default_privacy IS NOT NULL
        """,
        skip_no_result=True,
    )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env, "calendar", "20.0.1.1/noupdate_changes.xml")
    # the events without calendar get the primary calendar of their organizer
    env["calendar.event"].with_context(active_test=False).search(
        [("calendar_id", "=", False), ("user_id", "!=", False)]
    )._compute_calendar_id()
    _default_privacy(env.cr)
