# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Partner customizations',
    'version': '10.0.1.0.0',
    'depends': [
        'base',
    ],
    'author': "Comunitea",
    'license': "AGPL-3",
    'summary': '''Several customizations on partner models''',
    'website': 'http://www.comunitea.com',
    'data': ['views/res_harbor_view.xml',
             'views/res_partner_view.xml',
             'views/res_company_view.xml',
             'security/ir.model.access.csv'],
    'installable': True,
    'auto_install': False,
}
