# -*- coding: utf-8 -*-
# © 2016 Comunitea - Santi Argüeso<santi@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'JIM Partner Risk Multicompany',
    'version': '10.0.1.0.0',
    'author': 'Comunitea ',
    "category": "Custom",
    'license': 'AGPL-3',
    'depends': [
        'partner_financial_risk',
        'partner_sale_risk',
        'jim_sale'
    ],
    'contributors': [
        "Comunitea ",
        "Santi Argüeso <santi@comunitea.com>",
        "Kiko Sánchez <kiko@comunitea.com>",

    ],
    "data": [
        'views/res_partner.xml',
        'views/sale_view.xml',
    ],
    "installable": True
}
