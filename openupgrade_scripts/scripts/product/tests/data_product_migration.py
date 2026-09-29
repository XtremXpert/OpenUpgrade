env = locals().get("env")

pricelist = env["product.pricelist"].create({"name": "OpenUpgrade pricelist"})
Item = env["product.pricelist.item"]
Item.create(
    {
        "name": "OpenUpgrade percentage rule",
        "pricelist_id": pricelist.id,
        "applied_on": "3_global",
        "compute_price": "percentage",
        "percent_price": 12.5,
    }
)
Item.create(
    {
        "name": "OpenUpgrade formula discount rule",
        "pricelist_id": pricelist.id,
        "applied_on": "3_global",
        "compute_price": "formula",
        "base": "list_price",
        "price_discount": 10,
        "price_surcharge": 2,
    }
)
Item.create(
    {
        "name": "OpenUpgrade formula markup rule",
        "pricelist_id": pricelist.id,
        "applied_on": "3_global",
        "compute_price": "formula",
        "base": "standard_price",
        "price_discount": -20,
    }
)

# supplier info with a unit
template = env["product.template"].create({"name": "OpenUpgrade product"})
env["product.supplierinfo"].create(
    {
        "partner_id": env.ref("base.res_partner_1").id,
        "product_tmpl_id": template.id,
        "product_uom_id": env.ref("uom.product_uom_dozen").id,
        "price": 42,
    }
)

# attribute values excluded for each other
attribute = env["product.attribute"].create(
    {
        "name": "OpenUpgrade attribute",
        "value_ids": [
            (0, 0, {"name": "OpenUpgrade A"}),
            (0, 0, {"name": "OpenUpgrade B"}),
        ],
    }
)
attribute2 = env["product.attribute"].create(
    {
        "name": "OpenUpgrade attribute 2",
        "value_ids": [
            (0, 0, {"name": "OpenUpgrade X"}),
            (0, 0, {"name": "OpenUpgrade Y"}),
        ],
    }
)
variants = env["product.template"].create(
    {
        "name": "OpenUpgrade variants",
        "attribute_line_ids": [
            (
                0,
                0,
                {
                    "attribute_id": attribute.id,
                    "value_ids": [(6, 0, attribute.value_ids.ids)],
                },
            ),
            (
                0,
                0,
                {
                    "attribute_id": attribute2.id,
                    "value_ids": [(6, 0, attribute2.value_ids.ids)],
                },
            ),
        ],
    }
)
value_a = variants.attribute_line_ids[0].product_template_value_ids.filtered(
    lambda v: v.name == "OpenUpgrade A"
)
value_x = variants.attribute_line_ids[1].product_template_value_ids.filtered(
    lambda v: v.name == "OpenUpgrade X"
)
env["product.template.attribute.exclusion"].create(
    {
        "product_template_attribute_value_id": value_a.id,
        "product_tmpl_id": variants.id,
        "value_ids": [(6, 0, value_x.ids)],
    }
)

# base unit of website_sale
if "website.base.unit" in env:
    env["website.base.unit"].create({"name": "OpenUpgrade base unit"})
env.cr.commit()
