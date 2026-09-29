env = locals().get("env")

# a company using a document layout that became a table design
env["res.company"].create(
    {
        "name": "OpenUpgrade bold company",
        "external_report_layout_id": env.ref("web.external_layout_bold").id,
    }
)
env.cr.commit()
