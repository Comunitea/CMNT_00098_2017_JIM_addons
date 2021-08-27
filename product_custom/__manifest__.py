# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product customizations",
    "version": "14.0.1.0.0",
    "depends": ["jim_stock", "js_addons", "product_dimension"],
    "author": "Comunitea",
    "license": "AGPL-3",
    "summary": """Several customizations on product models""",
    "website": "http://www.comunitea.com",
    "data": [
        "views/product_web_report.xml",
        "views/product_category.xml",
        "views/account_invoice_report_view.xml",
        "views/product_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
