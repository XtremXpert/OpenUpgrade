env = locals().get("env")

# custom access rights and record rules, to be converted to ir.access
group = env["res.groups"].create(
    {
        "name": "OpenUpgrade test group",
        "implied_ids": [(4, env.ref("base.group_user").id)],
    }
)
category_model = env.ref("base.model_res_partner_category")
industry_model = env.ref("base.model_res_partner_industry")
env["ir.model.access"].create(
    {
        "name": "OpenUpgrade test access",
        "model_id": category_model.id,
        "group_id": group.id,
        "perm_read": True,
        "perm_write": True,
        "perm_create": False,
        "perm_unlink": False,
    }
)
env["ir.rule"].create(
    {
        "name": "OpenUpgrade test group rule",
        "model_id": category_model.id,
        "groups": [(4, group.id)],
        "domain_force": "[('name', 'ilike', 'openupgrade')]",
        "perm_read": True,
        "perm_write": False,
        "perm_create": False,
        "perm_unlink": False,
    }
)
env["ir.rule"].create(
    {
        "name": "OpenUpgrade test global rule",
        "model_id": category_model.id,
        "domain_force": "[('name', '!=', 'secret')]",
    }
)
# a custom group rule restricting a standard access right
env["ir.rule"].create(
    {
        "name": "OpenUpgrade test rule on standard access",
        "model_id": industry_model.id,
        "groups": [(4, env.ref("base.group_user").id)],
        "domain_force": "[('name', '!=', 'hidden')]",
        "perm_read": True,
        "perm_write": False,
        "perm_create": False,
        "perm_unlink": False,
    }
)
# a standard access right deactivated by the administrator
env.ref("base.access_res_partner_industry_group_system").active = False

# res.bank data to be moved to res.partner.bank
bank = env["res.bank"].create(
    {
        "name": "OpenUpgrade test bank",
        "bic": "OPUPCAM1",
        "city": "Montréal",
        "country": env.ref("base.ca").id,
    }
)
env["res.partner.bank"].create(
    {
        "acc_number": "OPENUPGRADE-TEST-123",
        "partner_id": env.ref("base.main_partner").id,
        "bank_id": bank.id,
    }
)

# client action params: Binary to Json
env["ir.actions.client"].create(
    {
        "name": "OpenUpgrade test client action",
        "tag": "openupgrade_test",
        "params": {"openupgrade": 1},
    }
)

# zip_required to zip_applicability
env["res.country"].create(
    {"name": "OpenUpgrade Testland", "code": "XT", "zip_required": False}
)

# ir.model.fields.index: boolean to selection
env["ir.model.fields"].create(
    {
        "name": "x_openupgrade_test",
        "model_id": category_model.id,
        "field_description": "OpenUpgrade test field",
        "ttype": "char",
        "index": True,
    }
)
env.cr.commit()
