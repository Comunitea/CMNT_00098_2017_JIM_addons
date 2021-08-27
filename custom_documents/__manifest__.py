# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Custom documents",
    "summary": "Report customizations",
    "version": "14.0.1.0.0",
    "category": "Uncategorized",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "sale",
        "sale_stock",
        "sale_margin",
        "delivery",
        "account_payment_sale",
        "stock_picking_invoice_link",
        "partner_consolidate",
        "stock_picking_report_valued",
        "purchase",
        "telesale",
        "sale_global_discount",
        "report_wkhtmltopdf_param",
        "js_reports"
    ],
    "data": [
        "views/product.xml",
        "views/stock_picking.xml",
        "views/sale_order.xml",
        "views/account.xml",
        "data/stock_mail_template.xml",
        "data/sale_mail_template.xml",
    ],
}
