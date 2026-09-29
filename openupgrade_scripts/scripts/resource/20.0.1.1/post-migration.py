# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _resources_without_calendar(env):
    """
    calendar_id is required now. A resource without calendar worked flexible
    hours in Odoo 19: give it an 'undefined' calendar of its company.
    """
    Resource = env["resource.resource"].with_context(active_test=False)
    resources = Resource.search([("calendar_id", "=", False)])
    if not resources:
        return
    Calendar = env["resource.calendar"].with_context(active_test=False)
    for company, company_resources in resources.grouped("company_id").items():
        calendar = Calendar.search(
            [("calendar_type", "=", "undefined"), ("company_id", "=", company.id)],
            limit=1,
        )
        if not calendar:
            calendar = Calendar.create(
                {
                    "name": env._("Flexible hours"),
                    "calendar_type": "undefined",
                    "company_id": company.id,
                }
            )
        company_resources.write({"calendar_id": calendar.id})
        _logger.info(
            "%s resources of company %s without calendar now use the flexible "
            "calendar %s",
            len(company_resources),
            company.display_name,
            calendar.display_name,
        )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env, "resource", "20.0.1.1/noupdate_changes.xml")
    _resources_without_calendar(env)
