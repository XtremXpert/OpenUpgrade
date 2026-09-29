# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

# The certification templates were redesigned: the colored variants became a
# 'company' (colors of the company) or a 'black' variant of each design.
_layouts = [
    ("classic_blue", "classic-1_company"),
    ("classic_gold", "classic-1_company"),
    ("classic_purple", "classic-1_company"),
    ("modern_blue", "modern_company"),
    ("modern_gold", "modern_company"),
    ("modern_purple", "modern_company"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.map_values(
        env.cr,
        "certification_report_layout",
        "certification_report_layout",
        _layouts,
        table="survey_survey",
    )
