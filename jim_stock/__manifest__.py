# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Jim Stock",
    "version": "11.0.1.0.0",
    "author": "Comunitea ",
    "category": "Custom",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "delivery",
        "mrp",
        "telesale",
        "base_delivery_carrier_label",
    ],
    "contributors": ["Comunitea ", "Javier Colmenero <javier@comunitea.com>"],
    "data": [
        "views/product_view.xml",
        "views/stock_view.xml",
        "views/company_view.xml",
        "views/route_view.xml",
        #'views/product_web_view.xml',
        "security/stock_security.xml",
        "wizard/stock_picking_return.xml",
        "wizard/stock_import.xml",
        "wizard/stock_export.xml",
        "views/stock_in_out.xml",
        "views/account_invoice.xml",
        "views/mrp_bom.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
