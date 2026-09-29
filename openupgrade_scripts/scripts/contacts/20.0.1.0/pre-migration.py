# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

# menu moved from base_address_extended
_moved_xmlids = [
    ("base_address_extended.menu_res_city", "contacts.menu_res_city"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, _moved_xmlids)
