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
        'sales_team',
        'sale_order_dates',
        'product',
    ],
    'contributors': [
        "Comunitea ",
        "Javier Colmenero <javier@comunitea.com>"
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/customer_price.xml',
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/stock_picking.xml',
        'views/res_partner_view.xml',
        'report/report_stock_forecast.xml',
        'security/jim_sale_security.xml'
    ],
    "installable": True
}
