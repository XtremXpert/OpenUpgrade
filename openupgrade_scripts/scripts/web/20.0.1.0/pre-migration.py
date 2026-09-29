# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

# The Bold, Boxed and Striped document layouts are gone: they became table
# designs (res.company.report_tables_id) applied on the Light layout.
_layouts_to_tables = {
    "web.external_layout_bold": "bold",
    "web.external_layout_boxed": "boxed",
    "web.external_layout_striped": "striped",
}


def _company_report_layouts(env):
    """Run before the views are deleted so that the companies using them can
    be mapped instead of losing their layout."""
    standard = env.ref("web.external_layout_standard", raise_if_not_found=False)
    if not standard:
        return
    for xmlid, table_design in _layouts_to_tables.items():
        view = env.ref(xmlid, raise_if_not_found=False)
        if not view:
            continue
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE res_company
            SET external_report_layout_id = %s, report_tables_id = %s
            WHERE external_report_layout_id = %s
            """,
            (standard.id, table_design, view.id),
        )


@openupgrade.migrate()
def migrate(env, version):
    _company_report_layouts(env)
