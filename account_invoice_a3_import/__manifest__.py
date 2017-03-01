# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'A3 invoice format import',
    'version': '10.0.1.0.0',
    'depends': [
        'account_payment_partner',
        'account_invoice_tag'
    ],
    'author': "Comunitea",
    'license': "AGPL-3",
    'summary': '''Allow to import A3 invoices importation format''',
    'website': 'http://www.comunitea.com',
    'data': ['views/a3_import_log_view.xml',
             'views/res_partner_view.xml',
             'views/res_company_view.xml',
             'data/a3_import_data.xml',
             'security/ir.model.access.csv'],
    'installable': True,
    'auto_install': False,
}
