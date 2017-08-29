# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.addons.stock.models.product import OPERATORS


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _search_global_real_stock(self, operator, value):
        domain = [('global_real_stock', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    def _search_global_avail_stock(self, operator, value):
        domain = [('global_available_stock', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    global_real_stock = fields.Float('Global Real Stock',
                                     compute='_compute_global_stock',
                                     digits=dp.get_precision
                                     ('Product Unit of Measure'),
                                     help="Real stock in all companies.",
                                     search='_search_global_real_stock')
    global_available_stock = fields.Float('Global Available Stock',
                                          compute='_compute_global_stock',
                                          digits=dp.get_precision
                                          ('Product Unit of Measure'),
                                          help="Real stock minus outgoing "
                                          " in all companies.",
                                          search='_search_global_avail_stock')

    @api.multi
    def _compute_global_stock(self):

        for template in self:
            global_real_stock = 0.0
            global_available_stock = 0.0
            for p in template.product_variant_ids:
                global_real_stock += p.global_real_stock
                global_available_stock += p.global_available_stock
            template.global_real_stock = global_real_stock
            template.global_available_stock = global_available_stock


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def _get_web_stock(self):
        bom_obj = self.env["mrp.bom"]
        bom_line_obj = self.env["mrp.bom.line"]
        for product in self:
            stock = product.global_available_stock
            if product.bom_count:
                boms = \
                    bom_obj.search(['|', '&',
                                    ('product_tmpl_id', '=',
                                     product.product_tmpl_id.id),
                                    ('product_id', '=', False),
                                    ('product_id', '=', product.id)])
                for bom in boms:
                    min_qty = 0
                    for line in bom.bom_line_ids:
                        qty = line.product_id.global_available_stock / \
                            line.product_qty
                        if not min_qty or qty < min_qty:
                            min_qty = qty
                    if min_qty < 0:
                        min_qty = 0
                    stock += (min_qty * bom.product_qty)
            else:
                bom_lines = bom_line_obj.\
                    search([('product_id', '=', product.id)])
                for line in bom_lines:
                    if line.product_qty:
                        stock += \
                            line.bom_id.product_tmpl_id.\
                            global_available_stock * line.product_qty
            product.web_global_stock = int(stock)

    def _search_global_product_quantity(self, operator, value, field):
        if field not in ('global_available_stock', 'global_real_stock'):
            raise UserError(_('Invalid domain left operand %s') % field)
        if operator not in ('<', '>', '=', '!=', '<=', '>='):
            raise UserError(_('Invalid domain operator %s') % operator)
        if not isinstance(value, (float, int)):
            raise UserError(_('Invalid domain right operand %s') % value)

        ids = []
        for product in self.search([]):
            if OPERATORS[operator](product[field], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _search_global_real_stock(self, operator, value):
        if value == 0.0 and operator in ('=', '>=', '<='):
            return self._search_global_product_quantity(operator, value,
                                                        'global_real_stock')
        product_ids = self.sudo().\
            _search_qty_available_new(operator, value,
                                      self._context.get('lot_id'),
                                      self._context.get('owner_id'),
                                      self._context.get('package_id'))
        return [('id', 'in', product_ids)]

    def _search_global_avail_stock(self, operator, value):
        return self.\
            _search_global_product_quantity(operator, value,
                                            'global_available_stock')

    global_real_stock = fields.Float('Global Real Stock',
                                     compute='_compute_global_stock',
                                     digits=dp.get_precision
                                     ('Product Unit of Measure'),
                                     help="Real stock in all companies.",
                                     search='_search_global_real_stock')
    global_available_stock = fields.Float('Global Available Stock',
                                          compute='_compute_global_stock',
                                          digits=dp.get_precision
                                          ('Product Unit of Measure'),
                                          help="Real stock minus outgoing "
                                          " in all companies.",
                                          search='_search_global_avail_stock')
    web_global_stock = fields.Float('Web stock', readonly=True,
                                    digits=dp.get_precision
                                    ('Product Unit of Measure'),
                                    compute="_get_web_stock")

    @api.multi
    def _compute_global_stock(self):
        order_line_obj = self.env["sale.order.line"]
        deposit_ids = \
            self.env['stock.location'].sudo().search([('deposit', '=', True)]).ids
        company_ids = \
            self.env['res.company'].sudo().search([('no_stock', '=', True)]).ids

        self._cr.execute(
            "SELECT SOL.product_id, sum(SOL.product_uom_qty) as qty FROM "
            "sale_order_line SOL " 
            "INNER JOIN sale_order  SO ON SO.id = SOL.order_id "
            "INNER JOIN stock_location_route SLR  ON SLR.id = SOL.route_id "
            "WHERE SOL.product_id in %s "
            "AND SO.state in ('lqdr', 'pending', 'progress_lqdr', 'progress',"
            " 'proforma') "
            "AND not SLR.no_stock group BY SOL.product_id",
                                   [tuple(self.ids)])
        sale_line_data = dict(self._cr.fetchall())

        for product in self:
            ctx = self._context.copy()
            deposit_real_stock = 0
            deposit_available_stock = 0
            sale_lines_stock = 0
            global_real_stock = product.sudo().qty_available
            global_available_stock = product.sudo().qty_available - \
                product.sudo().outgoing_qty

            # Get stock global in deposit location to discount it
            if deposit_ids:
                ctx.update({'location': deposit_ids})
                deposit_real_stock = \
                    product.with_context(ctx).sudo().qty_available
                deposit_available_stock = \
                    product.with_context(ctx).sudo().qty_available - \
                    product.with_context(ctx).sudo().outgoing_qty
            company_real_stock = 0
            company_available_stock = 0
            if company_ids:
                for company in company_ids:
                    ctx = self._context.copy()
                    ctx.update({'force_company': company})
                    company_real_stock += \
                        product.with_context(ctx).sudo().qty_available
                    company_available_stock += \
                        product.with_context(ctx).sudo().qty_available - \
                        product.with_context(ctx).sudo().outgoing_qty

            # slines = order_line_obj.sudo().search([('product_id', '=', product.id),
            #                                 ('order_id.state', 'in',
            #                                  ['lqdr', 'pending',
            #                                   'progress_lqdr', 'progress',
            #                                   'proforma'])])
            # for sline in slines:
            #     if sline.route_id.no_stock == False:
            #         sale_lines_stock += sline.product_uom_qty
            sale_lines_stock = sale_line_data.get(product.id, 0)
            product.global_real_stock = global_real_stock - \
                                        deposit_real_stock -company_real_stock
            product.global_available_stock = \
                global_available_stock - deposit_available_stock - \
                sale_lines_stock - company_available_stock
