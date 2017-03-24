# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


{
    'name': 'Modulo JIM Sports SGA - Odoo',
    'version': '10.0',
    'author': 'Comunitea, ',
    "category": "",
    'license': 'AGPL-3',
    'description': 'Integracion SGA - Odoo',
    'depends': [
        'stock',
        'sale',
        'sale_stock'
    ],
    'contributors': [
        "Comunitea",
        "Kiko Sanchez<kiko@comunitea.com>",    ],
    "data": [
        'data/sga_data.xml',
        'views/sga_file.xml',
        'views/sga_views.xml',
        'views/sga_carrier.xml',
        'views/sga_sale_order.xml',
        'views/sga_purchase_order.xml',
        'views/sga_stock_picking.xml',

    ],
    "demo": [

    ],
    'test': [

    ],
    'installable': True
}
