# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

# record moved from crm_livechat
_moved_xmlids = [
    ("crm_livechat.utm_source_livechat", "utm.utm_source_livechat"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, _moved_xmlids)
