# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # the xmlid is reused by a server action now
    openupgrade.delete_records_safely_by_xml_id(
        env, ["mass_mailing.mailing_list_merge_action"]
    )
