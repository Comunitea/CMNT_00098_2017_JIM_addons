# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Jim Intercompany",
    "version": "14.0.1.0.0",
    "author": "Comunitea ",
    "category": "Custom",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "stock",
        "purchase",
        "sale_stock",
        "inter_company_rules",
        "mrp",
    ],
    "contributors": [
        "Comunitea ",
    ],
    "data": [
        "views/product_view.xml",
        "views/procurement_rule_view.xml",
        "views/sale_order_view.xml",
        "views/stock_picking.xml",
        "views/company_view.xml",
    ],
    "installable": True,
}
