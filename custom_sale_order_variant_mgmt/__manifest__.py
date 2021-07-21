# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Custom sale order variant management",
    "summary": "",
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
        "delivery",
        "sale_order_variant_mgmt",
        "chained_discount_commercial_rules",
        "jim_stock",
    ],
    "data": ["views/sale_order.xml", "security/ir.model.access.csv"],
}
