# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_renamed_fields = [
    ("website", "website", "send_abandoned_cart_email", "send_abandoned_cart_followup"),
    ("website", "website", "contact_us_button_url", "contact_us_link_url"),
]

# the shop page options moved from the categories to the website
_category_flags = (
    "show_category_title",
    "show_category_description",
    "align_category_content",
)


def _website_prevent_sale(env):
    """'Hide add to cart when price = 0' became prevent_sale + prevent_sale_for"""
    openupgrade.add_fields(
        env,
        [
            ("prevent_sale", "website", "website", "boolean", False, "website_sale"),
            (
                "prevent_sale_for",
                "website",
                "website",
                "selection",
                False,
                "website_sale",
            ),
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE website
        SET prevent_sale = COALESCE(prevent_zero_price_sale, FALSE),
            prevent_sale_for = 'zero_price'
        """,
    )


def _website_required_fields(cr):
    openupgrade.logged_query(
        cr,
        """
        UPDATE website SET show_line_subtotals_tax_selection = 'tax_excluded'
        WHERE show_line_subtotals_tax_selection IS NULL
        """,
    )


def _website_category_flags(env):
    """The category options are website options now: enable them on the
    website when a category used them"""
    openupgrade.add_fields(
        env,
        [
            (flag, "website", "website", "boolean", False, "website_sale")
            for flag in _category_flags
        ],
    )
    for flag in _category_flags:
        if not openupgrade.column_exists(env.cr, "product_public_category", flag):
            continue
        openupgrade.logged_query(
            env.cr,
            f"""
            UPDATE website
            SET {flag} = EXISTS (
                SELECT 1 FROM product_public_category category
                WHERE category.{flag}
                    AND (category.website_id IS NULL
                         OR category.website_id = website.id)
            )
            """,
        )


def _product_documents(cr):
    """The 'inside the quotation' option is gone and 'shown on product page'
    is an option of attached_on_sale now"""
    if not openupgrade.column_exists(cr, "product_document", "attached_on_sale"):
        return
    openupgrade.logged_query(
        cr,
        """
        UPDATE product_document SET attached_on_sale = 'quotation'
        WHERE attached_on_sale = 'inside'
        """,
    )
    if openupgrade.column_exists(cr, "product_document", "shown_on_product_page"):
        openupgrade.logged_query(
            cr,
            """
            UPDATE product_document SET attached_on_sale = 'shown_on_product_page'
            WHERE shown_on_product_page
            """,
        )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _renamed_fields)
    _website_prevent_sale(env)
    _website_required_fields(env.cr)
    _website_category_flags(env)
    _product_documents(env.cr)
