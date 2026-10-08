# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env, "mass_mailing", "20.0.2.7/noupdate_changes.xml")
    # the favorite filter became a list of dynamic lists
    openupgrade.m2o_to_x2m(
        env.cr,
        env["mailing.mailing"],
        "mailing_mailing",
        "mailing_filter_ids",
        "mailing_filter_id",
    )
