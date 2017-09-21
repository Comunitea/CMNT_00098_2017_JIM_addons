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

    tag_names = fields.Char('Tags', compute='_compute_tag_names', store=True)
    web = fields.Boolean('Web', compute="_compute_web_state", store=True)

    @api.depends('tag_ids')
    def _compute_web_state(self):
        for template in self:
            template.web = True in [x.web for x in template.tag_ids]
            for product in template.product_variant_ids:
                if product.force_web == 'yes':
                    product.web = True
                elif product.force_web == 'no':
                    product.web = False
                elif product.force_web == 'tags':
                    product.web = product.product_tmpl_id.web


    @api.depends('tag_ids')
    def _compute_tag_names(self):
        for product in self:
            product.tag_names = ', '.join(x.name for x in product.tag_ids)

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

    def _search_global_product_quantity(self, operator, value, field):
        if field not in ('global_available_stock', 'global_real_stock', 'web_global_stock'):
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

    def _search_global_avail_stock(self, operator, value):
        return self.\
            _search_global_product_quantity(operator, value,
                                            'global_available_stock')

    def _search_web_global_stock(self, operator, value):
        return self._search_global_product_quantity(operator, value,
                                                        'web_global_stock')

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
                                    compute="_compute_global_stock")
    tag_names = fields.Char('Tags', compute='_compute_tag_names', store=True)
    attribute_names = fields.Char('Attributes', compute='_compute_attribute_names', store=True)
    web = fields.Boolean('Web', compute="_compute_web_state", store=True)

    @api.depends('force_web')
    def _compute_web_state(self):
        for product in self:
            if product.force_web == 'yes':
                product.web = True
            elif product.force_web == 'no':
                product.web = False
            elif product.force_web == 'tags':
                product.web = product.product_tmpl_id.web

    @api.depends('tag_ids')
    def _compute_tag_names(self):
        for product in self:
            product.tag_names = ', '.join(x.name for x in product.tag_ids)

    @api.depends('attribute_value_ids')
    def _compute_attribute_names(self):
        for product in self:
            product.attribute_names = ', '.join(x.name_get()[0][1] for x in product.attribute_value_ids)

    @api.multi
    def _calculate_globals(self):
        not_deposit_ids = \
            self.env['stock.location'].sudo().search(
                [('deposit', '!=', True)]).ids
        company_ids = \
            self.env['res.company'].sudo().search(
                [('no_stock', '=', True)]).ids

        self._cr.execute(
            "SELECT SOL.product_id, sum(SOL.product_uom_qty) as qty FROM "
            "sale_order_line SOL "
            "INNER JOIN sale_order  SO ON SO.id = SOL.order_id "
            "INNER JOIN stock_location_route SLR  ON SLR.id = SOL.route_id "
            "WHERE SOL.product_id in %s "
            "AND SO.state in ('lqdr', 'pending', 'progress_lqdr', 'progress',"
            " 'proforma') "
            "AND not SLR.no_stock group BY SOL.product_id", [tuple(self.ids)])
        sale_line_data = dict(self._cr.fetchall())

        ctx = self._context.copy()
        ctx.update({'location': not_deposit_ids})
        qty_available_d = dict(
            [(p['id'], p['qty_available'])
             for p in self.sudo().read(['qty_available'])])
        outgoing_qty_d = dict(
            [(p['id'], p['outgoing_qty'])
             for p in self.sudo().read(['outgoing_qty'])])

        global_real_stock = qty_available_d
        global_available_stock = dict(
            [(p, qty_available_d[p] - outgoing_qty_d[p])
             for p in qty_available_d.keys()])

        company_real_stock = dict([(x.id, 0) for x in self])
        company_available_stock = dict([(x.id, 0) for x in self])
        if company_ids:
            for company in company_ids:
                ctx = self._context.copy()
                ctx.update({'force_company': company})
                company_available = dict(
                    [(p['id'], p['qty_available']) for p in
                     self.with_context(ctx).sudo().read(['qty_available'])])
                company_outgoing = dict(
                    [(p['id'], p['outgoing_qty']) for p in
                     self.with_context(ctx).sudo().read(['outgoing_qty'])])

                company_real_stock = {
                    k: company_real_stock.get(k, 0) +
                    company_available.get(k, 0)
                    for k in set(company_real_stock) | set(company_available)}

                company_available_stock_ = dict(
                    [(p, company_available[p] - company_outgoing[p])
                     for p in company_available.keys()])
                company_available_stock = {
                    k: company_available_stock.get(k, 0) +
                    company_available_stock_.get(k, 0)
                    for k in set(company_available_stock) |
                    set(company_available_stock_)}

        a = dict([(p, global_real_stock[p] -
                   company_real_stock[p])for p in self.ids])
        b = dict([
            (p, global_available_stock[p] - sale_line_data.get(p, 0) -
             company_available_stock[p])for p in self.ids])
        return dict(
            [(p, {'global_real_stock': a[p],
                  'global_available_stock': b[p]}) for p in self.ids])

    def _compute_global_stock(self):
        res = self._calculate_globals()

        bom_obj = self.env["mrp.bom"]
        bom_line_obj = self.env["mrp.bom.line"]
        for product in self:
            product.global_real_stock = res[product.id]['global_real_stock']
            product.global_available_stock = \
                res[product.id]['global_available_stock']
            stock = res[product.id]['global_available_stock']
            if product.bom_count:
                boms = \
                    bom_obj.search(['|', '&',
                                    ('product_tmpl_id', '=',
                                     product.product_tmpl_id.id),
                                    ('product_id', '=', False),
                                    ('product_id', '=', product.id)])
                for bom in boms:
                    min_qty = False
                    for line in bom.bom_line_ids:
                        if line.product_id.id in res:
                            global_available_stock = \
                                res[line.product_id.id][
                                  'global_available_stock']
                        else:
                            global_available_stock = \
                                line.product_id._calculate_globals()[
                                 line.product_id.id]['global_available_stock']
                        qty = global_available_stock / line.product_qty
                        if isinstance(min_qty, bool) or qty < min_qty:
                            min_qty = qty
                    if not min_qty or min_qty < 0:
                        min_qty = 0
                    stock += (min_qty * bom.product_qty)
            else:
                bom_lines = bom_line_obj.\
                    search([('product_id', '=', product.id)])
                for line in bom_lines:
                    if line.product_qty:
                        variants = line.bom_id.product_id or \
                            line.bom_id.product_tmpl_id.product_variant_ids
                        global_available_stock = sum(
                            [res[x.id]['global_available_stock']
                             if x in res
                             else x._calculate_globals()[x.id]
                             ['global_available_stock']
                             for x in variants])
                        stock += global_available_stock * line.product_qty
            product.web_global_stock = int(stock)
