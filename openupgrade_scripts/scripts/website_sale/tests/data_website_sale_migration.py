env = locals().get("env")

website = env["website"].search([], limit=1)
website.write(
    {
        "prevent_zero_price_sale": True,
        "send_abandoned_cart_email": True,
        "contact_us_button_url": "/openupgrade-contact",
    }
)
env["product.public.category"].create(
    {"name": "OpenUpgrade category", "show_category_title": True}
)

# an image of a variant
attribute = env["product.attribute"].create(
    {
        "name": "OpenUpgrade image attribute",
        "value_ids": [
            (0, 0, {"name": "OpenUpgrade red"}),
            (0, 0, {"name": "OpenUpgrade blue"}),
        ],
    }
)
template = env["product.template"].create(
    {
        "name": "OpenUpgrade imaged product",
        "attribute_line_ids": [
            (
                0,
                0,
                {
                    "attribute_id": attribute.id,
                    "value_ids": [(6, 0, attribute.value_ids.ids)],
                },
            )
        ],
    }
)
red = template.product_variant_ids.filtered(
    lambda variant: (
        "red" in variant.product_template_attribute_value_ids.mapped("name")[0]
    )
)
env["product.image"].create(
    {
        "name": "OpenUpgrade red image",
        "product_tmpl_id": template.id,
        "product_variant_id": red.id,
        "video_url": "https://www.youtube.com/watch?v=openupgrade",
    }
)
env.cr.commit()
