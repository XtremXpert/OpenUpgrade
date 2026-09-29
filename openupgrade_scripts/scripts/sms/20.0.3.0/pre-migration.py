# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _server_actions_sms_method(env):
    """
    'Send SMS' actions had a method: sms, sms with note, or note only. The
    method is gone (an SMS is always sent and logged): 'note only' actions
    become 'Log Note' actions carrying the body of their SMS template.
    """
    if not openupgrade.column_exists(env.cr, "ir_act_server", "log_note_note"):
        openupgrade.add_fields(
            env,
            [
                (
                    "log_note_note",
                    "ir.actions.server",
                    "ir_act_server",
                    "html",
                    "jsonb",
                    "mail",
                )
            ],
        )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_act_server action
        SET state = 'log_note',
            log_note_note = (
                SELECT jsonb_object_agg(lang, '<p>' || body || '</p>')
                FROM jsonb_each_text(template.body) AS translation(lang, body)
            )
        FROM sms_template template
        WHERE template.id = action.sms_template_id
            AND action.state = 'sms'
            AND action.sms_method = 'note'
        RETURNING action.id, action.name
        """,
    )
    for action_id, name in env.cr.fetchall():
        _logger.warning(
            "Server action %s (id %s) only logged a note from an SMS template: "
            "it now logs the static body of that template, review it",
            name,
            action_id,
        )


@openupgrade.migrate()
def migrate(env, version):
    _server_actions_sms_method(env)
