# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _payment_state(cr):
    """The 'in process' state is gone"""
    openupgrade.logged_query(
        cr,
        "UPDATE account_payment SET state = 'paid' WHERE state = 'in_process'",
    )


def _move_review_state(env):
    """The checked boolean became the review state"""
    openupgrade.add_fields(
        env,
        [
            (
                "review_state",
                "account.move",
                "account_move",
                "selection",
                False,
                "account",
            )
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move
        SET review_state = CASE WHEN checked THEN 'reviewed' ELSE 'no_review' END
        """,
    )


def _journal_groups(env):
    """
    A ledger group listed the journals it excluded; a journal now belongs to
    a single group. A journal joins the first group (by sequence) of its
    company that did not exclude it. The group name is unique globally now.
    """
    cr = env.cr
    openupgrade.add_fields(
        env,
        [
            (
                "journal_group_id",
                "account.journal",
                "account_journal",
                "many2one",
                False,
                "account",
            )
        ],
    )
    cr.execute("SELECT id, company_id FROM account_journal_group ORDER BY sequence, id")
    for group_id, company_id in cr.fetchall():
        openupgrade.logged_query(
            cr,
            """
            UPDATE account_journal journal
            SET journal_group_id = %(group)s
            WHERE journal.journal_group_id IS NULL
                AND (%(company)s IS NULL OR journal.company_id = %(company)s)
                AND NOT EXISTS (
                    SELECT 1 FROM account_journal_account_journal_group_rel rel
                    WHERE rel.account_journal_group_id = %(group)s
                        AND rel.account_journal_id = journal.id
                )
            """,
            {"group": group_id, "company": company_id},
            skip_no_result=True,
        )
    # unique name: suffix the duplicates with their company
    openupgrade.logged_query(
        cr,
        """
        UPDATE account_journal_group grp
        SET name = (
            SELECT jsonb_object_agg(lang, value || ' (' || company.name || ')')
            FROM jsonb_each_text(grp.name) AS translation(lang, value)
        )
        FROM res_company company
        WHERE company.id = grp.company_id AND grp.id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY name->>'en_US' ORDER BY sequence, id
                ) AS rn
                FROM account_journal_group
            ) duplicates WHERE rn > 1
        )
        """,
        skip_no_result=True,
    )


def _reports(env):
    """
    active became computed from a company dependent selection with a fallback
    boolean; foldable became the foldability selection.
    """
    if openupgrade.column_exists(env.cr, "account_report", "active"):
        openupgrade.add_fields(
            env,
            [
                (
                    "active_fallback",
                    "account.report",
                    "account_report",
                    "boolean",
                    False,
                    "account",
                )
            ],
        )
        openupgrade.logged_query(
            env.cr,
            "UPDATE account_report SET active_fallback = COALESCE(active, FALSE)",
        )
    if openupgrade.column_exists(env.cr, "account_report_line", "foldable"):
        openupgrade.add_fields(
            env,
            [
                (
                    "foldability",
                    "account.report.line",
                    "account_report_line",
                    "selection",
                    False,
                    "account",
                )
            ],
        )
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE account_report_line
            SET foldability = CASE
                WHEN foldable THEN 'foldable' ELSE 'always_unfolded'
            END
            """,
        )


def _account_groups(cr):
    """
    account.group is gone: accounts are organised with parent_id instead.
    The groups were computed from code prefixes, so no data is lost; they
    are only logged.
    """
    if not openupgrade.table_exists(cr, "account_group"):
        return
    cr.execute("SELECT COUNT(*) FROM account_group")
    count = cr.fetchone()[0]
    if count:
        _logger.warning(
            "%s account groups are not migrated: Odoo 20 uses parent accounts "
            "(account.account.parent_id) instead of groups by code prefix",
            count,
        )


@openupgrade.migrate()
def migrate(env, version):
    _payment_state(env.cr)
    _move_review_state(env)
    _journal_groups(env)
    _reports(env)
    _account_groups(env.cr)
