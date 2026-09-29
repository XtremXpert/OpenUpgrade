"""Encode any known changes to the database here
to help the matching process
"""

renamed_modules = {
    "website_sale_autocomplete": "website_address_autocomplete",
}

merged_modules = {
    "account_add_gln": "account",
    "account_peppol_advanced_fields": "account_peppol",
    "account_peppol_response": "account_peppol",
    "base_iban": "base",
    "base_vat": "account",
    "delivery_mondialrelay": "delivery",
    "delivery_stock_picking_batch": "stock_delivery",
    "hr_holidays_homeworking": "hr_holidays",
    "hr_homeworking": "hr",
    "hr_homeworking_calendar": "hr_calendar",
    "hr_hourly_cost": "hr",
    "hr_org_chart": "hr",
    "hr_work_entry_holidays": "hr_holidays",
    "l10n_cn_city": "l10n_cn",
    "l10n_dk_nemhandel": "l10n_dk",
    "l10n_dk_nemhandel_response": "l10n_dk",
    "l10n_dk_oioubl": "l10n_dk",
    "l10n_ec_stock": "l10n_ec",
    "l10n_fr_hr_work_entry_holidays": "l10n_fr_hr_holidays",
    "l10n_hu_edi_receive": "l10n_hu_edi",
    "l10n_latam_base": "base",
    "l10n_lk_invoice": "l10n_lk",
    "l10n_pl_bank_verification": "l10n_pl",
    "l10n_ro_cpv_code": "l10n_ro_edi",
    "l10n_ro_edi_stock_batch": "l10n_ro_edi_stock",
    "l10n_sa_withholding_tax": "l10n_sa",
    "l10n_tr_nilvera": "l10n_tr",
    "l10n_tr_nilvera_base_vat": "l10n_tr",
    "l10n_tr_nilvera_edispatch": "l10n_tr",
    "l10n_tr_nilvera_einvoice": "l10n_tr",
    "l10n_tr_nilvera_einvoice_extended": "l10n_tr",
    "l10n_uy_pos": "l10n_uy",
    "mrp_subcontracting_repair": "mrp_subcontracting",
    "pos_restaurant_adyen": "pos_adyen",
    "pos_restaurant_stripe": "pos_stripe",
    "pos_self_order_adyen": "pos_adyen",
    "pos_self_order_stripe": "pos_stripe",
    "pos_self_order_viva_com": "pos_viva_com",
    "purchase_requisition_sale": "purchase_requisition",
    "stock_picking_batch": "stock",
    "transifex": "base",
    "website_sale_collect_wishlist": "website_sale_collect",
    "website_sale_comparison": "website_sale",
    "website_sale_comparison_wishlist": "website_sale",
    "website_sale_mondialrelay": "website_sale",
    "website_sale_stock_wishlist": "website_sale_stock",
    "website_sale_wishlist": "website_sale",
}

renamed_models = {}

merged_models = {}
