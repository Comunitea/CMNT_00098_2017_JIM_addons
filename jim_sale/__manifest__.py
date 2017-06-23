# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Jim Sale',
    'version': '10.0.0.0.0',
    'author': 'Comunitea ',
    "category": "Custom",
    'license': 'AGPL-3',
    'depends': [
        'sale_stock',
        'sale_order_dates',
        'product'
    ],
    'contributors': [
        "Comunitea ",
        "Javier Colmenero <javier@comunitea.com>"
    ],
    "data": [
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/stock_picking.xml',
        'report/report_stock_forecast.xml',

    ],
    "installable": True
}
