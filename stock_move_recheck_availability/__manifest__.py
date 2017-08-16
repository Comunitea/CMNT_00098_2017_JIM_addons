# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stock move reheck avalibitlity.',
    'version': '10.0.1.0.0',
    'depends': [
        'stock'
    ],
    'author': "Comunitea",
    'license': "AGPL-3",
    'summary': '''Allow stock move line recheck avaulability line x line''',
    'website': 'http://www.comunitea.com',
    'data': [
        'views/stock_picking.xml',
             ],
    'installable': True,
    'auto_install': False,
}
