env = locals().get("env")

partner_model = env.ref("base.model_res_partner")
template = env["sms.template"].create(
    {
        "name": "OpenUpgrade SMS template",
        "model_id": partner_model.id,
        "body": "OpenUpgrade SMS body",
    }
)
for method in ("note", "sms"):
    env["ir.actions.server"].create(
        {
            "name": f"OpenUpgrade SMS {method} action",
            "model_id": partner_model.id,
            "state": "sms",
            "sms_template_id": template.id,
            "sms_method": method,
        }
    )
env.cr.commit()
