# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
Working schedules changed shape in Odoo 20:

- the boolean flexible_hours / two_weeks_calendar became calendar_type
  (undefined / variable / fixed);
- a calendar in two weeks mode is now a 'variable' calendar whose attendances
  are dated and repeat every two weeks;
- attendance lines have no section or lunch lines anymore, and a
  'duration based' attendance has no hours;
- time_type of leaves became count_as.
"""

import datetime
import logging
import math

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# Monday of an even week (see ResourceCalendarAttendance.get_week_type in
# Odoo 19): the dated attendances of the two weeks calendars start there.
_ANCHOR = datetime.date(2026, 1, 5)


def _week_type(date):
    """Parity of the week, as computed by Odoo 19."""
    return int(math.floor((date.toordinal() - 1) / 7) % 2)


def _first_date(dayofweek, week_type):
    date = _ANCHOR + datetime.timedelta(days=int(dayofweek))
    if _week_type(date) != int(week_type):
        date += datetime.timedelta(days=7)
    return date


def _calendar_type(env):
    openupgrade.add_fields(
        env,
        [
            (
                "calendar_type",
                "resource.calendar",
                "resource_calendar",
                "selection",
                False,
                "resource",
            )
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE resource_calendar
        SET calendar_type = CASE
            WHEN flexible_hours OR schedule_type = 'flexible' THEN 'undefined'
            WHEN two_weeks_calendar THEN 'variable'
            ELSE 'fixed'
        END
        """,
    )
    # an undefined calendar has no attendance lines
    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM resource_calendar_attendance
        WHERE calendar_id IN (
            SELECT id FROM resource_calendar WHERE calendar_type = 'undefined'
        )
        """,
    )


def _resources_without_calendar(cr):
    """
    calendar_id is required now: the ORM would give the calendar of the
    company to the resources without calendar, which worked flexible hours
    in Odoo 19. Give them an 'undefined' calendar of their company instead.
    """
    cr.execute(
        """
        SELECT DISTINCT company_id FROM resource_resource
        WHERE calendar_id IS NULL
        """
    )
    for (company_id,) in cr.fetchall():
        cr.execute(
            """
            SELECT id FROM resource_calendar
            WHERE calendar_type = 'undefined' AND company_id IS NOT DISTINCT FROM %s
            ORDER BY id LIMIT 1
            """,
            (company_id,),
        )
        row = cr.fetchone()
        if row:
            calendar_id = row[0]
        else:
            cr.execute(
                """
                INSERT INTO resource_calendar
                    (name, calendar_type, company_id, active, hours_per_day,
                     hours_per_week, full_time_required_hours, schedule_type, tz,
                     create_uid, create_date, write_uid, write_date)
                VALUES (%s, 'undefined', %s, TRUE, 8, 40, 40, 'flexible', 'UTC',
                        1, now(), 1, now())
                RETURNING id
                """,
                (openupgrade.get_legacy_name("flexible"), company_id),
            )
            calendar_id = cr.fetchone()[0]
        openupgrade.logged_query(
            cr,
            """
            UPDATE resource_resource SET calendar_id = %s
            WHERE calendar_id IS NULL AND company_id IS NOT DISTINCT FROM %s
            """,
            (calendar_id, company_id),
        )


def _attendances(env):
    cr = env.cr
    openupgrade.add_fields(
        env,
        [
            (
                "date",
                "resource.calendar.attendance",
                "resource_calendar_attendance",
                "date",
                False,
                "resource",
            ),
            (
                "recurrency",
                "resource.calendar.attendance",
                "resource_calendar_attendance",
                "boolean",
                False,
                "resource",
            ),
            (
                "recurrency_type",
                "resource.calendar.attendance",
                "resource_calendar_attendance",
                "selection",
                False,
                "resource",
            ),
            (
                "recurrency_interval",
                "resource.calendar.attendance",
                "resource_calendar_attendance",
                "integer",
                False,
                "resource",
            ),
            (
                "recurrency_end_type",
                "resource.calendar.attendance",
                "resource_calendar_attendance",
                "selection",
                False,
                "resource",
            ),
            (
                "recurrency_count",
                "resource.calendar.attendance",
                "resource_calendar_attendance",
                "integer",
                False,
                "resource",
            ),
            (
                "recurrency_until",
                "resource.calendar.attendance",
                "resource_calendar_attendance",
                "date",
                False,
                "resource",
            ),
        ],
    )
    # section and lunch lines are gone
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM resource_calendar_attendance
        WHERE display_type = 'line_section' OR day_period = 'lunch'
        """,
    )
    # duration based calendars: the attendances have a duration but no hours
    openupgrade.logged_query(
        cr,
        """
        UPDATE resource_calendar_attendance att
        SET hour_from = 0, hour_to = 0
        FROM resource_calendar cal
        WHERE cal.id = att.calendar_id AND cal.duration_based
        """,
    )
    # the duration must be positive
    openupgrade.logged_query(
        cr,
        """
        UPDATE resource_calendar_attendance
        SET duration_hours = hour_to - hour_from
        WHERE COALESCE(duration_hours, 0) <= 0 AND hour_to > hour_from
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM resource_calendar_attendance
        WHERE COALESCE(duration_hours, 0) <= 0 OR duration_hours > 24
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE resource_calendar_attendance
        SET recurrency = FALSE, recurrency_interval = 1,
            recurrency_end_type = 'forever', recurrency_count = 1
        """,
    )
    # two weeks calendars: dated attendances repeating every two weeks
    cr.execute(
        """
        SELECT att.id, att.dayofweek, att.week_type
        FROM resource_calendar_attendance att
        JOIN resource_calendar cal ON cal.id = att.calendar_id
        WHERE cal.calendar_type = 'variable'
        """
    )
    rows = cr.fetchall()
    for attendance_id, dayofweek, week_type in rows:
        cr.execute(
            """
            UPDATE resource_calendar_attendance
            SET date = %s, recurrency = TRUE, recurrency_type = 'weeks',
                recurrency_interval = 2, recurrency_end_type = 'forever',
                recurrency_until = '9999-12-31'
            WHERE id = %s
            """,
            (_first_date(dayofweek, week_type or "0"), attendance_id),
        )
    if rows:
        _logger.info(
            "%s attendances of two weeks calendars converted to dated "
            "attendances repeating every two weeks from %s",
            len(rows),
            _ANCHOR,
        )


def _leaves_count_as(env):
    openupgrade.rename_fields(
        env,
        [
            (
                "resource.calendar.leaves",
                "resource_calendar_leaves",
                "time_type",
                "count_as",
            )
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE resource_calendar_leaves
        SET count_as = CASE count_as
            WHEN 'leave' THEN 'absence' WHEN 'other' THEN 'working_time'
            ELSE count_as
        END
        WHERE count_as IN ('leave', 'other')
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    _calendar_type(env)
    _resources_without_calendar(env.cr)
    _attendances(env)
    _leaves_count_as(env)
