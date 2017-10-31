# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sequence en lineas de ventas, albaranes y facturas',
    'version': '10.0.1.0.0',
    'depends': [
        'jim_sale',
        'jim_purchase',
    ],
    'author': "Comunitea",
    'license': "AGPL-3",
    'summary': '''Sequencias en plantillas y reorden''',
    'website': 'http://www.comunitea.com',
    'data': ['security/ir.model.access.csv',
             'views/product_template.xml'
    ],
    'installable': True,
    'auto_install': False,
}
