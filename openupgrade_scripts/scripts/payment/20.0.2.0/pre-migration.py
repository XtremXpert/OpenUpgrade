# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
A payment method now belongs to a single provider (provider_id, unique with
the code) instead of being shared between providers; each provider module
defines its own copies of the methods. A provider is active / live instead of
having a state.
"""

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_method_columns = (
    "name",
    "code",
    "sequence",
    "primary_payment_method_id",
    "active",
    "image",
    "image_payment_form",
    "support_tokenization",
    "support_express_checkout",
    "support_manual_capture",
    "support_refund",
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
)


def _provider_state(env):
    openupgrade.add_fields(
        env,
        [
            (
                "active",
                "payment.provider",
                "payment_provider",
                "boolean",
                False,
                "payment",
            ),
            (
                "is_live",
                "payment.provider",
                "payment_provider",
                "boolean",
                False,
                "payment",
            ),
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE payment_provider
        SET active = COALESCE(state, 'disabled') != 'disabled',
            is_live = state = 'enabled'
        """,
    )


def _existing_columns(cr, table, columns):
    return [
        column for column in columns if openupgrade.column_exists(cr, table, column)
    ]


def _method_providers(cr):
    """The providers of each method: the old many2many, and the providers of
    the transactions and tokens using the method."""
    cr.execute(
        """
        SELECT payment_method_id, payment_provider_id
        FROM payment_method_payment_provider_rel
        UNION
        SELECT payment_method_id, provider_id FROM payment_transaction
        WHERE payment_method_id IS NOT NULL AND provider_id IS NOT NULL
        UNION
        SELECT payment_method_id, provider_id FROM payment_token
        WHERE payment_method_id IS NOT NULL AND provider_id IS NOT NULL
        ORDER BY 1, 2
        """
    )
    providers = {}
    for method_id, provider_id in cr.fetchall():
        providers.setdefault(method_id, []).append(provider_id)
    return providers


def _split_methods_by_provider(env):
    cr = env.cr
    openupgrade.add_fields(
        env,
        [
            (
                "provider_id",
                "payment.method",
                "payment_method",
                "many2one",
                False,
                "payment",
            )
        ],
    )
    providers = _method_providers(cr)
    columns = _existing_columns(cr, "payment_method", _method_columns)
    column_list = ", ".join(columns)
    copies = {}  # (method_id, provider_id) -> method id for that provider
    for method_id, provider_ids in providers.items():
        first, *others = provider_ids
        cr.execute(
            "UPDATE payment_method SET provider_id = %s WHERE id = %s",
            (first, method_id),
        )
        copies[(method_id, first)] = method_id
        for provider_id in others:
            cr.execute(
                f"""
                INSERT INTO payment_method ({column_list}, provider_id)
                SELECT {column_list}, %s FROM payment_method WHERE id = %s
                RETURNING id
                """,
                (provider_id, method_id),
            )
            copies[(method_id, provider_id)] = cr.fetchone()[0]
    # brands point to the copy of their primary method for the same provider
    for (method_id, provider_id), copy_id in copies.items():
        cr.execute(
            "SELECT primary_payment_method_id FROM payment_method WHERE id = %s",
            (copy_id,),
        )
        primary_id = cr.fetchone()[0]
        if primary_id and (primary_id, provider_id) in copies:
            cr.execute(
                "UPDATE payment_method SET primary_payment_method_id = %s WHERE id = %s",
                (copies[(primary_id, provider_id)], copy_id),
            )
    # transactions and tokens use the copy of their provider
    for table in ("payment_transaction", "payment_token"):
        for (method_id, provider_id), copy_id in copies.items():
            if copy_id != method_id:
                openupgrade.logged_query(
                    cr,
                    f"""
                    UPDATE {table} SET payment_method_id = %s
                    WHERE payment_method_id = %s AND provider_id = %s
                    """,
                    (copy_id, method_id, provider_id),
                    skip_no_result=True,
                )
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM payment_method
        WHERE provider_id IS NULL AND id NOT IN (
            SELECT primary_payment_method_id FROM payment_method
            WHERE primary_payment_method_id IS NOT NULL AND provider_id IS NOT NULL
        )
        """,
    )
    return copies


def _method_xmlids(cr, copies):
    """
    The methods were data of the payment module (payment.payment_method_<code>);
    each provider module now defines its own (payment_<provider>.payment_method_<code>).
    Give the module's xmlid to the record of its provider so that the module
    does not create a duplicate; the xmlid is noupdate so that a method the
    module does not define anymore is kept.
    """
    cr.execute(
        """
        SELECT data.id, data.name, data.res_id
        FROM ir_model_data data
        WHERE data.module = 'payment' AND data.model = 'payment.method'
            AND data.name LIKE 'payment_method_%%'
        """
    )
    xmlids = {res_id: (data_id, name) for data_id, name, res_id in cr.fetchall()}
    cr.execute("SELECT id, code FROM payment_provider")
    provider_codes = dict(cr.fetchall())
    cr.execute(
        "SELECT name FROM ir_module_module WHERE state IN ('installed', 'to upgrade', 'to install')"
    )
    modules = {row[0] for row in cr.fetchall()}
    handled = set()
    for (method_id, provider_id), copy_id in sorted(copies.items()):
        if method_id not in xmlids:
            continue
        data_id, name = xmlids[method_id]
        module = f"payment_{provider_codes.get(provider_id)}"
        if module not in modules:
            continue
        if copy_id == method_id:
            cr.execute(
                """
                UPDATE ir_model_data SET module = %s, noupdate = TRUE
                WHERE id = %s
                """,
                (module, data_id),
            )
        else:
            openupgrade.add_xmlid(
                cr, module, name, "payment.method", copy_id, noupdate=True
            )
        handled.add(method_id)
    # the methods without provider module keep their xmlid, they are noupdate
    _logger.info(
        "%s payment methods of the payment module moved to their provider module",
        len(handled),
    )


@openupgrade.migrate()
def migrate(env, version):
    _provider_state(env)
    copies = _split_methods_by_provider(env)
    _method_xmlids(env.cr, copies)
