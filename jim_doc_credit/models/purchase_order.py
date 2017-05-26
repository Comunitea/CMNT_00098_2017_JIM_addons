# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.exceptions import Warning

class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    @api.depends('proforma_invoice_ref', 'proforma_invoice_date',
                           'limit_expedition_date', 'mail_confirm_packing_list',
                           'partner_bank_contact_id', 'expire_credit_letter_date',
                           'incoterm_id', 'doc_credit_bank_id', 'in_port_id')
    def check_doc_credit_ok(self):
        fields_to_check = ('proforma_invoice_ref', 'proforma_invoice_date',
                           'limit_expedition_date', 'mail_confirm_packing_list',
                           'partner_bank_contact_id', 'expire_credit_letter_date',
                           'incoterm_id', 'doc_credit_bank_id', 'in_port_id')
        for field in fields_to_check:
            if not self[field]:
                return False
        return True

    doc_credit_ok = fields.Boolean("doc credit ok", compute="check_doc_credit_ok")
    allow_doc_credit = fields.Boolean("Documentary credit")
    limit_expedition_date = fields.Datetime("Limit expedition date")
    expire_credit_letter_date = fields.Datetime("Expire letter credit date")
    partner_bank_contact_id = fields.Many2one("res.partner", "Bank contact")
    mail_confirm_packing_list = fields.Char("Mail to send p/l", help="Mail a la que se envia la copia de la factura y el packing list")
    proforma_invoice_ref = fields.Char("Proforma invoice")
    proforma_invoice_date = fields.Datetime("Proforma invoice date")
    doc_credit_bank_id = fields.Many2one("res.bank", "Doc credit bank")
    in_port_id = fields.Many2one("res.partner", "In port")
