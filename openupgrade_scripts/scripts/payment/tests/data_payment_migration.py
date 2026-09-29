env = locals().get("env")

Provider = env["payment.provider"]
company = env.ref("base.main_company")
live = Provider.create(
    {
        "name": "OpenUpgrade live provider",
        "code": "none",
        "state": "enabled",
        "company_id": company.id,
    }
)
test = Provider.create(
    {
        "name": "OpenUpgrade test provider",
        "code": "none",
        "state": "test",
        "company_id": company.id,
    }
)
Provider.create(
    {
        "name": "OpenUpgrade disabled provider",
        "code": "none",
        "state": "disabled",
        "company_id": company.id,
    }
)
# a method shared by two providers, with a brand
shared = env["payment.method"].create(
    {
        "name": "OpenUpgrade shared method",
        "code": "openupgrade_shared",
        "provider_ids": [(6, 0, (live + test).ids)],
    }
)
env["payment.method"].create(
    {
        "name": "OpenUpgrade brand",
        "code": "openupgrade_brand",
        "primary_payment_method_id": shared.id,
        "provider_ids": [(6, 0, (live + test).ids)],
    }
)
# a method used by a token of the test provider only
token_method = env["payment.method"].create(
    {"name": "OpenUpgrade token method", "code": "openupgrade_token"}
)
env["payment.token"].create(
    {
        "provider_id": test.id,
        "payment_method_id": token_method.id,
        "partner_id": env.ref("base.main_partner").id,
        "payment_details": "OpenUpgrade token",
        "provider_ref": "openupgrade",
    }
)
# an unused method
env["payment.method"].create(
    {"name": "OpenUpgrade unused method", "code": "openupgrade_unused"}
)
env.cr.commit()
