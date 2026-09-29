# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def _sale_delay_company_dependent(cr):
    """The delivery lead time is the same for every company of the product
    (all the companies when the product is shared)"""
    legacy = openupgrade.get_legacy_name("sale_delay")
    if not openupgrade.column_exists(cr, "product_template", legacy):
        return
    openupgrade.logged_query(
        cr,
        f"""
        UPDATE product_template template
        SET sale_delay = (
            SELECT jsonb_object_agg(company.id::text, template.{legacy})
            FROM res_company company
            WHERE template.company_id IS NULL OR company.id = template.company_id
        )
        WHERE COALESCE(template.{legacy}, 0) != 0
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    _sale_delay_company_dependent(env.cr)
    openupgrade.load_data(env, "sale", "20.0.1.2/noupdate_changes.xml")
