# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Documentary credit',
    'version': '10.0.1.0.0',
    'depends': [
        'purchase',
        'purchase_advance_payment',
        'res_currency_fixed_rate',
        'shipping_container'
    ],
    'author': "Comunitea",
    'license': "AGPL-3",
    'summary': '''Documentary credit customization''',
    'website': 'http://www.comunitea.com',
    'data': ['views/purchase_order.xml',
             'views/purchase_advance_payment_wzd_view.xml',
             'views/doc_credit.xml',
             'views/account_payment.xml',
             'views/res_currency.xml',
             'reports/report_doc_credit.xml'
             ],
    'installable': True,
    'auto_install': False,
}
