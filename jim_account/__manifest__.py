# -*- coding: utf-8 -*-
# © 2016 Comunitea - Santi Argüeso<santi@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Jim Account',
    'version': '10.0.1.0.0',
    'author': 'Comunitea ',
    "category": "Custom",
    'license': 'AGPL-3',
    'depends': [
        'account_banking_mandate',
        'account_invoice_refund_link'
    ],
    'contributors': [
        "Comunitea ",
        "Santi Argüeso <santi@comunitea.com>",

    ],
    "data": [
        'views/account_move.xml',
        'views/account_banking_mandate.xml',
        'views/account_invoice.xml',
        'views/res_partner.xml'
    ],
    "installable": True
}
