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
        'views/crm_claim_type.xml',
        'views/crm_claim.xml',
        'wizard/crm_claim_rma_make_refund_view.xml',
        'wizard/crm_claim_rma_make_batch_refund_view.xml',
    ],
    "installable": True
}
