# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_renamed_fields = [
    ("website.page", "website_page", "date_publish", "publish_on"),
]

_social_fields = (
    "social_twitter",
    "social_facebook",
    "social_github",
    "social_linkedin",
    "social_youtube",
    "social_instagram",
    "social_tiktok",
    "social_discord",
)


def _view_visibility(cr):
    """visibility is required now, and the empty value became 'public'"""
    openupgrade.logged_query(
        cr,
        """
        UPDATE ir_ui_view SET visibility = 'public'
        WHERE visibility IS NULL OR visibility = ''
        """,
    )
    if openupgrade.column_exists(cr, "website_controller_page", "visibility"):
        openupgrade.logged_query(
            cr,
            """
            UPDATE website_controller_page SET visibility = 'public'
            WHERE visibility IS NULL OR visibility = ''
            """,
        )


def _menu_manual_url(env):
    """The stored url became a computed field: the url of the page, or the
    url entered by the user, now stored in manual_url"""
    openupgrade.add_fields(
        env, [("manual_url", "website.menu", "website_menu", "char", False, "website")]
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE website_menu SET manual_url = url
        WHERE page_id IS NULL AND controller_page_id IS NULL
            AND url IS NOT NULL AND url NOT IN ('', '#')
        """,
    )


def _rewrite_required_fields(cr):
    openupgrade.logged_query(
        cr,
        "UPDATE website_rewrite SET redirect_type = '301' WHERE redirect_type IS NULL",
    )
    openupgrade.logged_query(
        cr,
        "UPDATE website_rewrite SET url_from = '' WHERE url_from IS NULL",
    )


def _social_links_to_company(cr):
    """The social accounts of a website are gone; keep them on the company
    when the company has none"""
    for field in _social_fields:
        if not openupgrade.column_exists(cr, "website", field):
            continue
        openupgrade.logged_query(
            cr,
            f"""
            UPDATE res_company company SET {field} = website.{field}
            FROM website
            WHERE website.company_id = company.id
                AND company.{field} IS NULL
                AND website.{field} IS NOT NULL
            """,
        )


@openupgrade.migrate()
def migrate(env, version):
    _view_visibility(env.cr)
    openupgrade.rename_fields(env, _renamed_fields)
    _menu_manual_url(env)
    _rewrite_required_fields(env.cr)
    _social_links_to_company(env.cr)
