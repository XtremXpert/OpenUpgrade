# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_renamed_fields = [
    ("product.template", "product_template", "expense_policy", "reinvoice_policy"),
]


def _invoice_policy_required(cr):
    openupgrade.logged_query(
        cr,
        """
        UPDATE product_template SET invoice_policy = 'order'
        WHERE invoice_policy IS NULL
        """,
    )


def _customer_lead_integer(cr):
    """The lead time is a number of days now"""
    cr.execute(
        """
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'sale_order_line' AND column_name = 'customer_lead'
        """
    )
    if cr.fetchone()[0] != "integer":
        openupgrade.logged_query(
            cr,
            """
            ALTER TABLE sale_order_line
                ALTER COLUMN customer_lead TYPE integer
                    USING ROUND(COALESCE(customer_lead, 0))::integer
            """,
        )


def _campaign_invoiced_amount_float(cr):
    cr.execute(
        """
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'utm_campaign' AND column_name = 'invoiced_amount'
        """
    )
    row = cr.fetchone()
    if row and row[0] == "integer":
        openupgrade.logged_query(
            cr,
            """
            ALTER TABLE utm_campaign
                ALTER COLUMN invoiced_amount TYPE double precision
            """,
        )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _renamed_fields)
    _invoice_policy_required(env.cr)
    _customer_lead_integer(env.cr)
    _campaign_invoiced_amount_float(env.cr)
