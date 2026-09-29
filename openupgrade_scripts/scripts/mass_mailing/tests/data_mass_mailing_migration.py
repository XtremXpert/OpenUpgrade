env = locals().get("env")

mailing_filter = env["mailing.filter"].create(
    {
        "name": "OpenUpgrade filter",
        "mailing_domain": "[('email', 'ilike', 'openupgrade')]",
        "mailing_model_id": env.ref("mass_mailing.model_mailing_contact").id,
    }
)
env["mailing.mailing"].create(
    {
        "subject": "OpenUpgrade mailing",
        "mailing_model_id": env.ref("mass_mailing.model_mailing_contact").id,
        "mailing_filter_id": mailing_filter.id,
        "mailing_domain": "[('email', 'ilike', 'openupgrade')]",
    }
)
env.cr.commit()
