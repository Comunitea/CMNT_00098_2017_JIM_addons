# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _


class ProcurementRule(models.Model):
    """ Pull rules """
    _inherit = 'procurement.rule'

    procure_method = fields.Selection(
        selection_add=[('company', 'According to Product Company')])
    ic_picking_type_id = fields.Many2one(
        'stock.picking.type', 'IC Picking Type ',
        required=True,
        help="Picking Type for Intercompany purchase, ...")

    @api.model
    def _get_action(self):
        res = super(ProcurementRule, self)._get_action()
        res.append(('intercompany_buy', _('Intercompany Buy')))
        res.append(('product_company', _('Intercompany Buy or Move According to Product Company')))
        return res


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    @api.model
    def create(self, values):
        if self.env.context.get('user_company'):
            values.update({'company_id': self.env.context.get('user_company')})
        print "Crea Abastecimiento "
        print values
        return super(ProcurementOrder, self).create(values)

    def _get_stock_move_values(self):
        vals = super(ProcurementOrder, self)._get_stock_move_values()
        if vals['procure_method'] == 'company':
            if self.env['product.product'].browse(vals['product_id']).\
                    company_id.id == vals['company_id']:
                vals['procure_method'] = 'make_to_stock'
            else:
                vals['procure_method'] = 'make_to_order'
        return vals

    @api.multi
    def _run(self):
        if self.rule_id and self.rule_id.action == 'product_company':
            if self.company_id.id == self.product_id.company_id.id:
                # get teh product only with move
                if not self.rule_id.location_src_id:
                    self.message_post(body=_('No source location defined!'))
                    return False
                # create the move as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
                move = self.env['stock.move'].sudo().create(self._get_stock_move_values())
                move.action_confirm()
                return True
            else:
                # if product belongs to another compamy generate intercompany_buy
                return self.make_intercompany_buy_po()

        if self.rule_id and self.rule_id.action == 'intercompany_buy':
            return self.po_or_ic_po()

        return super(ProcurementOrder, self)._run()

    @api.multi
    def po_or_ic_po(self):
        if self.company_id.id == self.product_id.company_id.id:
            return self.make_po()
        else:
            return self.make_intercompany_buy_po()

    @api.multi
    def make_intercompany_buy_po(self):
        """
        COPY OF MAKE PO except buy:
        * Partner id from prodcut company
        * Price for intercomany_price of product.product
        These changes are commented, the other is the original code
        """
        cache = {}
        res = []

        for procurement in self:
            print ('Compra intercompany %s') % (procurement.company_id.name)
            if not procurement.product_id.company_id:
                procurement.message_post(body=_('No company to product %s. \
                    Please set one to fix this procurement.')
                                         % (procurement.product_id.name))
                continue

            # CHANGED, GET PARTNER FROM PRODUCT COMPANY
            partner = procurement.product_id.company_id.partner_id

            gpo = procurement.rule_id.group_propagation_option
            group = (gpo == 'fixed' and procurement.rule_id.group_id) or \
                    (gpo == 'propagate' and procurement.group_id) or False

            domain = (
                ('partner_id', '=', partner.id),
                ('state', '=', 'draft'),
                ('picking_type_id', '=',
                 procurement.rule_id.picking_type_id.id),
                ('company_id', '=', procurement.company_id.id),
                ('dest_address_id', '=', procurement.partner_dest_id.id))
            if group:
                domain += (('group_id', '=', group.id),)

            if domain in cache:
                po = cache[domain]
            else:
                po = self.env['purchase.order'].search([dom for dom in domain])
                po = po[0] if po else False
                cache[domain] = po
            auto_confirm = False
            if not po:
                vals = procurement._prepare_purchase_order(partner)
                vals['intercompany'] = True
                vals['picking_type_id'] = procurement.rule_id.ic_picking_type_id \
                                            and  procurement.rule_id.ic_picking_type_id.id \
                                            or procurement.rule_id.picking_type_id.id
                po = self.env['purchase.order'].create(vals)
                name = (procurement.group_id and (procurement.group_id.name + ":") or "") + (procurement.name != "/" and procurement.name or procurement.move_dest_id.raw_material_production_id and procurement.move_dest_id.raw_material_production_id.name or "")
                message = _("This purchase order has been created from: \
                    <a href=# data-oe-model=procurement.order \
                    data-oe-id=%d>%s</a>") % (procurement.id, name)
                po.message_post(body=message)
                cache[domain] = po

               # auto_confirm=True

            elif not po.origin or procurement.origin not in po.origin.split(', '):
                # Keep track of all procurements
                if po.origin:
                    if procurement.origin:
                        po.write({'origin': po.origin + ', ' +
                                 procurement.origin})
                    else:
                        po.write({'origin': po.origin})
                else:
                    po.write({'origin': procurement.origin})
                name = (self.group_id and (self.group_id.name + ":") or "") + (self.name != "/" and self.name or self.move_dest_id.raw_material_production_id and self.move_dest_id.raw_material_production_id.name or "")
                po.message_post(body=message)
            if po:
                res += [procurement.id]

            # Create Line
            po_line = False
            for line in po.order_line:
                if line.product_id == procurement.product_id and line.product_uom == procurement.product_id.uom_po_id:
                    procurement_uom_po_qty = procurement.product_uom.\
                        _compute_quantity(procurement.product_qty,
                                          procurement.product_id.uom_po_id)
                    # CHANGED, GET PRICE UNIT FROM NEW FIELD
                    intercompany_price = line.product_id.intercompany_price
                    price_unit = self.env['account.tax'].\
                        _fix_tax_included_price(intercompany_price,
                                                line.product_id.supplier_taxes_id,
                                                line.taxes_id)

                    po_line = line.write({
                        'product_qty': line.product_qty + procurement_uom_po_qty,
                        'price_unit': price_unit,
                        'procurement_ids': [(4, procurement.id)]
                    })
                    break
            if not po_line:
                # CHANGED, SUPPLIER BY PARTNER
                vals = procurement.\
                    _prepare_intercompany_purchase_line(po, partner)
                # CHANGED, GET PRICE UNIT FROM NEW FIELD
                prod = procurement.product_id
                taxes = prod.supplier_taxes_id
                fpos = po.fiscal_position_id
                taxes_id = fpos.map_tax(taxes) if fpos else taxes
                if taxes_id:
                    taxes_id = taxes_id.\
                        filtered(lambda x: x.company_id.id == po.company_id.id)
                vals['price_unit'] = self.env['account.tax'].\
                    _fix_tax_included_price(prod.intercompany_price,
                                            prod.supplier_taxes_id, taxes_id)
                self.env['purchase.order.line'].create(vals)

            # # CHANGED, AUTOMATIC CONFIRMATION
            # if auto_confirm:
            #     po.button_confirm()
        return res

    @api.multi
    def _prepare_intercompany_purchase_line(self, po, partner):
        """
        COPIED FROM _prepare_purchase_order_line method
        * Removed seller
        * Get intercompay price from product
        """
        self.ensure_one()
        procurement_uom_po_qty = self.product_uom.\
            _compute_quantity(self.product_qty, self.product_id.uom_po_id)

        taxes = self.product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes) if fpos else taxes
        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id ==
                                         self.company_id.id)

        price_unit = self.env['account.tax'].\
            _fix_tax_included_price(self.product_id.intercompany_price,
                                    self.product_id.supplier_taxes_id,
                                    taxes_id)

        product_lang = self.product_id.with_context({
            'lang': partner.lang,
            'partner_id': partner.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        date_planned = self.date_planned
        return {
            'name': name,
            'product_qty': procurement_uom_po_qty,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id.ids)],
            'procurement_ids': [(4, self.id)],
            'order_id': po.id,
        }

class MakeProcurement(models.TransientModel):
    _inherit = 'make.procurement'

    @api.multi
    def make_procurement(self):
        """ Creates procurement order for selected product. """
        return super(MakeProcurement, self.with_context(user_company=self.env.user.company_id.id)).make_procurement()


