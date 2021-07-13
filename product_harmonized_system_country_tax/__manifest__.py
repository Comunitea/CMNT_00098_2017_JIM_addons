# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Product hscode country tax",
    "version": "11.0.1.0.0",
    "author": "Comunitea ",
    "category": "Custom",
    "license": "AGPL-3",
    "depends": ["purchase", "product_harmonized_system"],
    "contributors": [
        "Comunitea ",
        "Kiko Sanchez <kiko@comunitea.com>",
    ],
    "data": [
        "views/hs_code.xml",
        "views/purchase_order.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
