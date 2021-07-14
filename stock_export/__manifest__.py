# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Stock Export",
    "version": "12.0.1.0.0",
    "author": "Comunitea ",
    "category": "Custom",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "sale_stock",
    ],
    "contributors": ["Comunitea ", "Kiko Sánchez <kiko@comunitea.com>"],
    "data": ["security/ir.model.access.csv", "data/export_stock.xml"],
    "installable": True,
}
