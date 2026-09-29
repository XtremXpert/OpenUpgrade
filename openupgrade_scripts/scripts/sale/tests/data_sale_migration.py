env = locals().get("env")

product = env["product.product"].create(
    {
        "name": "OpenUpgrade reinvoiced service",
        "type": "service",
        "expense_policy": "cost",
        "invoice_policy": "delivery",
    }
)
order = env["sale.order"].create(
    {
        "partner_id": env.ref("base.res_partner_1").id,
        "client_order_ref": "OpenUpgrade lead time",
        "order_line": [
            (
                0,
                0,
                {"product_id": product.id, "product_uom_qty": 1, "customer_lead": 2.6},
            )
        ],
    }
)
env.cr.commit()
