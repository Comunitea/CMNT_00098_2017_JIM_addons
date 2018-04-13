# -*- coding: utf-8 -*-
# © 2018 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Jim Purchase Forecast',
    'version': '10.0.1.0.0',
    'author': 'Comunitea ',
    "category": "Custom",
    'license': 'AGPL-3',
    'depends': [
        'jim_purchase',
        'purchase_advance_payment',
        'jim_sale',
        'jim_stock',

    ],
    'contributors': [
        "Comunitea ",
        "Javier Colmenero <javier@comunitea.com>",
    ],
    "data": [
        'views/purchase_forecast_view.xml',
        'security/ir.model.access.csv',

    ],
    "installable": True
}
