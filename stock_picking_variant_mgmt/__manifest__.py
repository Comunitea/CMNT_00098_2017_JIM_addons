# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Handle easily multiple variants on pickings",
    "summary": "Handle the addition/removal of multiple variants from "
    "product template into the stock picking",
    "version": "12.0.1.0.0",
    "author": "Tecnativa, Comunitea, " "Odoo Community Association (OCA)",
    "category": "Purchase",
    "license": "AGPL-3",
    "website": "http://www.comunitea.com",
    "depends": [
        "stock",
        "web_widget_x2many_2d_matrix",
    ],
    "demo": [],
    "data": [
        "wizard/stock_move_manage_variant_view.xml",
        "views/stock_picking.xml",
    ],
    "installable": True,
}
