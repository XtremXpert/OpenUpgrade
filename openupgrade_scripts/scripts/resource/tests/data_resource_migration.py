env = locals().get("env")

Calendar = env["resource.calendar"]
company = env.ref("base.main_company")

Calendar.create(
    {
        "name": "OpenUpgrade flexible calendar",
        "company_id": company.id,
        "flexible_hours": True,
        "hours_per_week": 30,
    }
)
Calendar.create(
    {
        "name": "OpenUpgrade fixed calendar",
        "company_id": company.id,
        "attendance_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "name": "Monday morning",
                    "dayofweek": "0",
                    "hour_from": 8,
                    "hour_to": 12,
                    "day_period": "morning",
                },
            ),
            (
                0,
                0,
                {
                    "name": "Monday lunch",
                    "dayofweek": "0",
                    "hour_from": 12,
                    "hour_to": 13,
                    "day_period": "lunch",
                },
            ),
            (
                0,
                0,
                {
                    "name": "Monday afternoon",
                    "dayofweek": "0",
                    "hour_from": 13,
                    "hour_to": 17,
                    "day_period": "afternoon",
                },
            ),
        ],
    }
)
two_weeks = Calendar.create(
    {
        "name": "OpenUpgrade two weeks calendar",
        "company_id": company.id,
        "two_weeks_calendar": True,
        "attendance_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "name": "First week",
                    "dayofweek": "0",
                    "display_type": "line_section",
                    "week_type": "0",
                    "sequence": 0,
                },
            ),
            (
                0,
                0,
                {
                    "name": "Monday (first week)",
                    "dayofweek": "0",
                    "hour_from": 8,
                    "hour_to": 12,
                    "day_period": "morning",
                    "week_type": "0",
                    "sequence": 1,
                },
            ),
            (
                0,
                0,
                {
                    "name": "Second week",
                    "dayofweek": "0",
                    "display_type": "line_section",
                    "week_type": "1",
                    "sequence": 10,
                },
            ),
            (
                0,
                0,
                {
                    "name": "Tuesday (second week)",
                    "dayofweek": "1",
                    "hour_from": 13,
                    "hour_to": 17,
                    "day_period": "afternoon",
                    "week_type": "1",
                    "sequence": 11,
                },
            ),
        ],
    }
)
env["resource.calendar.leaves"].create(
    {
        "name": "OpenUpgrade training",
        "calendar_id": two_weeks.id,
        "date_from": "2026-03-02 08:00:00",
        "date_to": "2026-03-02 17:00:00",
        "time_type": "other",
    }
)
resource = env["resource.resource"].create(
    {"name": "OpenUpgrade resource without calendar", "company_id": company.id}
)
# the default is the calendar of the company: a resource without calendar
# (fully flexible in Odoo 19) is only possible by hand
env.cr.execute(
    "UPDATE resource_resource SET calendar_id = NULL WHERE id = %s", (resource.id,)
)
env.cr.commit()
