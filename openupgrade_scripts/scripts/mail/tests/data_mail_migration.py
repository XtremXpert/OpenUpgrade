env = locals().get("env")

# activity type chaining
ActivityType = env["mail.activity.type"]
triggered = ActivityType.create({"name": "OpenUpgrade triggered type"})
suggested_late = ActivityType.create(
    {"name": "OpenUpgrade suggested type (late)", "sequence": 20}
)
suggested_first = ActivityType.create(
    {"name": "OpenUpgrade suggested type (first)", "sequence": 10}
)
ActivityType.create(
    {
        "name": "OpenUpgrade trigger type",
        "chaining_type": "trigger",
        "triggered_next_type_id": triggered.id,
    }
)
ActivityType.create(
    {
        "name": "OpenUpgrade suggest type",
        "chaining_type": "suggest",
        "suggested_next_type_ids": [(6, 0, (suggested_late + suggested_first).ids)],
    }
)

# server actions posting a note or a message from a template
partner_model = env.ref("base.model_res_partner")
template = env["mail.template"].create(
    {
        "name": "OpenUpgrade note template",
        "model_id": partner_model.id,
        "body_html": "<p>OpenUpgrade note body</p>",
    }
)
for method in ("note", "comment"):
    env["ir.actions.server"].create(
        {
            "name": f"OpenUpgrade {method} action",
            "model_id": partner_model.id,
            "state": "mail_post",
            "template_id": template.id,
            "mail_post_method": method,
        }
    )

# a starred message with a tracking value
partner = env.ref("base.main_partner")
message = env["mail.message"].create(
    {
        "model": "res.partner",
        "res_id": partner.id,
        "body": "<p>OpenUpgrade starred message</p>",
        "message_type": "notification",
        "starred_partner_ids": [(4, env.ref("base.partner_admin").id)],
    }
)
env["mail.tracking.value"].create(
    {
        "field_id": env.ref("base.field_res_partner__name").id,
        "mail_message_id": message.id,
        "old_value_char": "OpenUpgrade old name",
        "new_value_char": "OpenUpgrade new name",
    }
)
env.cr.commit()
