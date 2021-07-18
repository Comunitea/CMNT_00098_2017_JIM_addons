# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Jim purchase",
    "version": "13.0.1.0.0",
    "author": "Comunitea ",
    "category": "Custom",
    "license": "AGPL-3",
    "depends": [
        "purchase_advance_payment",
        "purchase_order_variant_mgmt",
        "jim_stock",
        "purchase_early_payment_discount",
        "sale_early_payment_discount",
    ],
    "contributors": [
        "Comunitea ",
        "Kiko Sanchez <kiko@comunitea.com>",
    ],
    "data": [
        "views/purchase_order.xml",
        "views/account_payment.xml",
        "wizard/product_purchase_wizard.xml",
        "wizard/purchase_invoice_wzd.xml",
        "views/product_view.xml",
        "views/res_company.xml",
    ],
    "installable": True,
}
