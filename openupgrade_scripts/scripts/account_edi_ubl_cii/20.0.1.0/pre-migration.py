# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_renamed_fields = [
    ("res.partner", "res_partner", "peppol_eas", "routing_scheme"),
    ("res.partner", "res_partner", "peppol_endpoint", "routing_endpoint"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _renamed_fields)
