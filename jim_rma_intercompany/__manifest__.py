# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Jim RMA Intercompany',
    'version': '10.0.0.0.0',
    'author': 'Comunitea ',
    "category": "Custom",
    'license': 'AGPL-3',
    'depends': [
        'jim_intercompany',
        'crm_claim',
    ],
    'contributors': [
        "Comunitea ",
    ],
    "data": [
        'views/wzd_claim_line_to_scrap.xml',
        'views/wzd_claim_make_picking.xml',
        'views/claim_make_picking.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml'
    ],
    "installable": True
}
