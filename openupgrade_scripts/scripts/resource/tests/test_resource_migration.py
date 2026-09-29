import datetime

from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestResourceMigration(TransactionCase):
    def _calendar(self, name):
        return self.env["resource.calendar"].search([("name", "=", name)])

    def test_flexible_calendar(self):
        calendar = self._calendar("OpenUpgrade flexible calendar")
        self.assertEqual(calendar.calendar_type, "undefined")
        self.assertFalse(calendar.attendance_ids)

    def test_fixed_calendar(self):
        calendar = self._calendar("OpenUpgrade fixed calendar")
        self.assertEqual(calendar.calendar_type, "fixed")
        self.assertEqual(len(calendar.attendance_ids), 2)
        self.assertEqual(
            set(calendar.attendance_ids.mapped("day_period")), {"morning", "afternoon"}
        )
        self.assertFalse(any(calendar.attendance_ids.mapped("date")))

    def test_two_weeks_calendar(self):
        calendar = self._calendar("OpenUpgrade two weeks calendar")
        self.assertEqual(calendar.calendar_type, "variable")
        attendances = calendar.attendance_ids.sorted("sequence")
        self.assertEqual(len(attendances), 2)
        first, second = attendances
        self.assertEqual(first.date, datetime.date(2026, 1, 5))
        self.assertEqual(first.dayofweek, "0")
        self.assertEqual(second.date, datetime.date(2026, 1, 13))
        self.assertEqual(second.dayofweek, "1")
        for attendance in attendances:
            self.assertTrue(attendance.recurrency)
            self.assertEqual(attendance.recurrency_type, "weeks")
            self.assertEqual(attendance.recurrency_interval, 2)
            self.assertEqual(attendance.recurrency_end_type, "forever")

    def test_leave_count_as(self):
        leave = self.env["resource.calendar.leaves"].search(
            [("name", "=", "OpenUpgrade training")]
        )
        self.assertEqual(leave.count_as, "working_time")

    def test_resource_without_calendar(self):
        resource = self.env["resource.resource"].search(
            [("name", "=", "OpenUpgrade resource without calendar")]
        )
        self.assertEqual(resource.calendar_id.calendar_type, "undefined")
        self.assertEqual(resource.calendar_id.company_id, resource.company_id)
