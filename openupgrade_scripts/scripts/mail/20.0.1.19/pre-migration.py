# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_renamed_fields = [
    ("mail.message", "mail_message", "starred_partner_ids", "bookmarked_partner_ids"),
]

_renamed_tables = [
    (
        "mail_message_res_partner_starred_rel",
        "mail_message_res_partner_bookmarked_rel",
    ),
]

# mail.tracking.value moved to the new module mail_tracking
_tracking_xmlids = [
    (
        "mail.action_view_mail_tracking_value",
        "mail_tracking.action_view_mail_tracking_value",
    ),
    ("mail.menu_mail_tracking_value", "mail_tracking.menu_mail_tracking_value"),
    (
        "mail.view_mail_tracking_value_form",
        "mail_tracking.view_mail_tracking_value_form",
    ),
    (
        "mail.view_mail_tracking_value_tree",
        "mail_tracking.view_mail_tracking_value_tree",
    ),
    (
        "mail.field_mail_message__tracking_value_ids",
        "mail_tracking.field_mail_message__tracking_value_ids",
    ),
    (
        "mail.field_mail_mail__tracking_value_ids",
        "mail_tracking.field_mail_mail__tracking_value_ids",
    ),
]


def _move_tracking_values_to_mail_tracking(cr):
    """
    mail.tracking.value now lives in mail_tracking, a new module that is not
    installed automatically: install it so that the tracking values survive.
    """
    openupgrade.logged_query(
        cr,
        """
        UPDATE ir_module_module SET state = 'to install'
        WHERE name = 'mail_tracking' AND state = 'uninstalled'
        """,
    )
    openupgrade.update_module_moved_models(
        cr, "mail.tracking.value", "mail", "mail_tracking"
    )
    openupgrade.rename_xmlids(cr, _tracking_xmlids)


def _tracking_message_type(cr):
    """Messages carrying tracking values now have their own message type."""
    openupgrade.logged_query(
        cr,
        """
        UPDATE mail_message
        SET message_type = 'tracking'
        WHERE message_type = 'notification'
            AND id IN (SELECT mail_message_id FROM mail_tracking_value)
        """,
    )


def _activity_type_chaining(env):
    """
    chaining_type (trigger / suggest), triggered_next_type_id and the
    suggested_next_type_ids many2many became the single suggested_next_type_id:
    keep the triggered type, or the first suggested type by sequence.
    """
    openupgrade.add_fields(
        env,
        [
            (
                "suggested_next_type_id",
                "mail.activity.type",
                "mail_activity_type",
                "many2one",
                False,
                "mail",
            )
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE mail_activity_type
        SET suggested_next_type_id = triggered_next_type_id
        WHERE chaining_type = 'trigger' AND triggered_next_type_id IS NOT NULL
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE mail_activity_type mat
        SET suggested_next_type_id = sub.recommended_id
        FROM (
            SELECT DISTINCT ON (rel.activity_id) rel.activity_id, rel.recommended_id
            FROM mail_activity_rel rel
            JOIN mail_activity_type t ON t.id = rel.recommended_id
            ORDER BY rel.activity_id, t.sequence, t.id
        ) sub
        WHERE sub.activity_id = mat.id
            AND mat.chaining_type = 'suggest'
            AND mat.suggested_next_type_id IS NULL
        """,
    )
    env.cr.execute(
        """
        SELECT t.id, t.name, COUNT(*)
        FROM mail_activity_type t
        JOIN mail_activity_rel rel ON rel.activity_id = t.id
        WHERE t.chaining_type = 'suggest'
        GROUP BY t.id, t.name
        HAVING COUNT(*) > 1
        """
    )
    for type_id, name, count in env.cr.fetchall():
        _logger.warning(
            "Activity type %s (id %s) suggested %s next activities, only the "
            "first one by sequence is kept in Odoo 20",
            name,
            type_id,
            count,
        )


def _server_actions_log_note(env):
    """
    'Send Message' actions had a method: email, message or note. Note is now
    a separate action type with a static note instead of a template: copy the
    template body (per language) so that the action keeps working.
    """
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
        SET state = 'log_note', log_note_note = template.body_html
        FROM mail_template template
        WHERE template.id = action.template_id
            AND action.state = 'mail_post'
            AND action.mail_post_method = 'note'
        RETURNING action.id, action.name
        """,
    )
    for action_id, name in env.cr.fetchall():
        _logger.warning(
            "Server action %s (id %s) logged a note from a mail template: it "
            "now logs the static body of that template, review it",
            name,
            action_id,
        )


def _channel_members_xmlids(env):
    """The membership of the admin in the general and admin channels is
    data of the module now: give the xmlids to the existing records."""
    partner = env.ref("base.partner_admin", raise_if_not_found=False)
    if not partner:
        return
    for channel_xmlid, member_xmlid in (
        ("mail.channel_all_employees", "channel_member_general_channel_for_admin"),
        ("mail.channel_admin", "channel_member_channel_admin_partner_admin"),
    ):
        channel = env.ref(channel_xmlid, raise_if_not_found=False)
        if not channel:
            continue
        env.cr.execute(
            """
            SELECT id FROM discuss_channel_member
            WHERE channel_id = %s AND partner_id = %s
            """,
            (channel.id, partner.id),
        )
        row = env.cr.fetchone()
        if row and not env.ref(f"mail.{member_xmlid}", raise_if_not_found=False):
            openupgrade.add_xmlid(
                env.cr, "mail", member_xmlid, "discuss.channel.member", row[0]
            )


@openupgrade.migrate()
def migrate(env, version):
    _move_tracking_values_to_mail_tracking(env.cr)
    _channel_members_xmlids(env)
    _tracking_message_type(env.cr)
    openupgrade.rename_tables(env.cr, _renamed_tables)
    openupgrade.rename_fields(env, _renamed_fields)
    _activity_type_chaining(env)
    _server_actions_log_note(env)
