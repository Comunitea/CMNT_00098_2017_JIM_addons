# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, models, fields


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.multi
    @api.depends('partner_id', 'partner_id.consolidate')
    def _get_commercial_partner(self):
        for inv in self:
            if inv.state != 'draft':
                self._cr.execute("""SELECT commercial_partner_id
                                    FROM account_invoice
                                    WHERE id = %s""" % str(inv.id))
                old_value = self._cr.fetchall()
                if old_value and old_value[0]:
                   inv.commercial_partner_id = old_value[0][0]
                continue
            if inv.partner_id.consolidate and inv.partner_id.parent_id:
                inv.commercial_partner_id = \
                    inv.partner_id.parent_id.commercial_partner_id
            else:
                if not inv.partner_id.parent_id:
                    inv.commercial_partner_id = \
                        inv.partner_id.commercial_partner_id
                else:
                    if inv.partner_id.parent_id.consolidate and \
                            inv.partner_id.parent_id.parent_id:
                        inv.commercial_partner_id = \
                            inv.partner_id.parent_id.parent_id
                    else:
                        inv.commercial_partner_id = \
                            inv.partner_id.commercial_partner_id


    commercial_partner_id = fields.Many2one('res.partner',
                                            string='Invoice to',
                                            related=None,
                                            related_field=None,
                                            compute='_get_commercial_partner',
                                            compute_sudo=True,
                                            store=True, readonly=True,
                                            help="The commercial entity that \
                                            will be used on Journal Entries \
                                            for this invoice")