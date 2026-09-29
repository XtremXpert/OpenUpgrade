env = locals().get("env")

website = env["website"].search([], limit=1)
website.write({"social_facebook": "https://facebook.com/openupgrade"})
website.company_id.write({"social_facebook": False})

view = env["ir.ui.view"].create(
    {
        "name": "OpenUpgrade test page",
        "type": "qweb",
        "arch": "<t t-name='openupgrade_test'><p>OpenUpgrade page</p></t>",
        "key": "website.openupgrade_test_page",
    }
)
page = env["website.page"].create(
    {
        "view_id": view.id,
        "url": "/openupgrade-test-page",
        "website_id": website.id,
        "date_publish": "2026-01-02 03:04:05",
        "is_published": True,
    }
)
env["website.menu"].create(
    {
        "name": "OpenUpgrade external menu",
        "url": "https://example.com/openupgrade",
        "website_id": website.id,
        "parent_id": website.menu_id.id,
    }
)
env["website.menu"].create(
    {
        "name": "OpenUpgrade page menu",
        "page_id": page.id,
        "website_id": website.id,
        "parent_id": website.menu_id.id,
    }
)
env.cr.commit()
