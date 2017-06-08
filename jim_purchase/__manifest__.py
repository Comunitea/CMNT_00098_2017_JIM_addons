# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Jim purchase',
    'version': '10.0.1.0.0',
    'author': 'Comunitea ',
    "category": "Custom",
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'purchase_advance_payment',

    ],
    'contributors': [
        "Comunitea ",
        "Kiko Sanchez <kiko@comunitea.com>",

    ],
    "data": [
        'views/purchase_order.xml',
        'views/account_payment.xml',

    ],
    "installable": True
}
