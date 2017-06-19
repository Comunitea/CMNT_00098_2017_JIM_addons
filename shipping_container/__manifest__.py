# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Shipping Container',
    'version': '10.0.1.0.0',
    'author': 'Comunitea ',
    "category": "Custom",
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'stock',

    ],
    'contributors': [
        "Comunitea ",
        "Kiko Sanchez <kiko@comunitea.com>",

    ],
    "data": [
        #'views/purchase_order.xml',
        'views/stock_picking.xml',
        'views/shipping_container.xml',
        'security/ir.model.access.csv'

    ],
    "installable": True
}
