# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Jim Stock',
    'version': '10.0.0.0.0',
    'author': 'Comunitea ',
    "category": "Custom",
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'delivery',
        'mrp',
        'telesale',
    ],
    'contributors': [
        "Comunitea ",
        "Javier Colmenero <javier@comunitea.com>"
    ],
    "data": [
        'views/product_view.xml',
        'views/stock_view.xml',
        'views/company_view.xml',
        'views/route_view.xml',
        #'views/product_web_view.xml',
        'security/stock_security.xml',
        'wizard/stock_picking_return.xml',
        'wizard/stock_import.xml',
        'wizard/stock_export.xml',
        'views/stock_in_out.xml',
        'views/account_invoice.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True
}
