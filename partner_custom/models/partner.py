# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):

    _inherit = "res.partner"

    harbor_ids = fields.Many2many("res.harbor", string="Harbors")
    # propietary = fields.\
    #    Char("Propietary", related="company_id.ref", readonly=True)
    web_password = fields.Char("Password web", size=32)
    default_contact_person = fields.Char("Contact person", size=90)
    invoice_in_paper = fields.Boolean()
    legacy_code = fields.Char()

    @api.model
    def create(self, vals):
        # if vals.get('type', 'contact') == 'delivery':
        #    vals['customer'] = False
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        # if vals.get('type', 'contact') == 'delivery':
        #    vals['customer'] = False
        return super(ResPartner, self).write(vals)

    @api.depends("email")
    def _compute_email_score(self):
        for partner in self.filtered("email"):
            partner.email_score = 50
            # partner.email_score = self.env['mail.tracking.email']. \
            #     email_score_from_email(partner.email)

    def _compute_opportunity_count(self):
        for partner in self:
            partner.opportunity_count = 0
            # operator = 'child_of' if partner.is_company else '='  # the opportunity count should counts the opportunities of this company and all its contacts
            # partner.opportunity_count = self.env['crm.lead'].search_count(
            #     [('partner_id', operator, partner.id),
            #      ('type', '=', 'opportunity')])

    def _rules_count(self):
        for partner in self:
            partner.rules_count = 0

    def _journal_item_count(self):
        for partner in self:
            partner.journal_item_count = 0
            partner.contracts_count = 0

    def _purchase_invoice_count(self):
        PurchaseOrder = self.env["purchase.order"]
        Invoice = self.env["account.invoice"]
        for partner in self:
            if partner.supplier:
                partner.purchase_order_count = PurchaseOrder.search_count(
                    [("partner_id", "child_of", partner.id)]
                )
                partner.supplier_invoice_count = Invoice.search_count(
                    [
                        ("partner_id", "child_of", partner.id),
                        ("type", "=", "in_invoice"),
                    ]
                )
            else:
                partner.purchase_order_count = 0
                partner.supplier_invoice_count = 0
