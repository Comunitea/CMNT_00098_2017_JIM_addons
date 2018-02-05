# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class purchase_order(models.Model):

    _inherit = "purchase.order"

    intercompany = fields.Boolean(string='Intercompany Purchase Order', copy=False)

    @api.multi
    def _get_destination_location(self):
        self.ensure_one()
        id = super(purchase_order, self)._get_destination_location()
        procurements = self.order_line.mapped('procurement_ids')
        loc_ids = procurements.mapped('location_id').mapped('id')
        if loc_ids:
            if id in loc_ids:
                return id
            else:
                return loc_ids[0]
        else:
            return id


    # Se hereda para
    @api.one
    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        """ Generate the Sale Order values from the PO
            :param name : the origin client reference
            :rtype name : string
            :param partner : the partner reprenseting the company
            :rtype partner : res.partner record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param direct_delivery_address : the address of the SO
            :rtype direct_delivery_address : res.partner record
        """
        partner_addr = partner.sudo().address_get(['invoice', 'delivery', 'contact'])
        warehouse = company.warehouse_id
        pricelist_obj = self.env['product.pricelist']
        pricelist_id = pricelist_obj.sudo()._get_partner_pricelist(
            partner.id, company.id)
        return {
            'name': self.env['ir.sequence'].sudo().next_by_code('sale.order') or '/',
            'company_id': company.id,
            'warehouse_id': warehouse.id,
            'client_order_ref': name,
            'partner_id': partner.id,
            'pricelist_id': pricelist_id,
            'partner_invoice_id': partner_addr['invoice'],
            'date_order': self.date_order,
            'fiscal_position_id': partner.property_account_position_id.id,
            'user_id': False,
            'auto_generated': True,
            'auto_purchase_order_id': self.id,
            'partner_shipping_id': direct_delivery_address or partner_addr['delivery']
        }

    @api.model
    def _prepare_sale_order_line_data(self, line, company, sale_id):
        vals = super(purchase_order, self)._prepare_sale_order_line_data(line, company, sale_id)
        if line.procurement_ids and line.procurement_ids[0].route_ids:
            vals['route_id'] = line.procurement_ids[0].route_ids[0].id
            vals['move_dest_IC_id'] = line.procurement_ids[0].move_dest_id.id \
                                      or False
            vals['purchase_line_IC'] = line.id
        return vals
