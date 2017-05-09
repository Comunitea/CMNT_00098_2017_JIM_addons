# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Jim Telesale',
    'version': '10.0.0.0.0',
    'author': 'Comunitea ',
    "category": "Custom",
    'license': 'AGPL-3',
    'depends': [
        'jim_sale',
        'jim_stock',
        'chained_discount_commercial_rules',
        'telesale_manage_variants',
    ],
    'contributors': [
        "Comunitea ",
        "Javier Colmenero <javier@comunitea.com>"
    ],
    "data": [
        'views/telesale_assets.xml'
    ],
    'qweb': [
        'static/src/xml/new_order_template.xml',
        'static/src/xml/order_history_template.xml',
        'static/src/xml/popups_template.xml',
    ],
    "installable": True
}
