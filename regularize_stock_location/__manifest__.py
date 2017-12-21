# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


{
    'name': 'Regularize stock location',
    'version': '10.0',
    'author': 'Comunitea, ',
    "category": "",
    'license': 'AGPL-3',
    'description': 'Allow regularize quants not reserve, list done moves to canceled moves ',
    'depends': ['jim_stock'
    ],
    'contributors': [
        "Comunitea",
        "Kiko Sanchez<kiko@comunitea.com>"]
    ,

    "data": [
        'wizard/regularize_location.xml',
        'wizard/return_dest_move_canceled.xml',
        'views/return_dest_move_canceled.xml',
        'views/done_dest_move_waiting.xml',
'views/product_stock_company_rel.xml',
        'views/stock_picking.xml',
        'security/ir.model.access.csv',
    ],
    "demo": [

    ],
    'test': [

    ],
    'installable': True
}

