# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from datetime import date


class WizardValuationHistory(models.TransientModel):
    _name = 'wzd.product.web'


    web_visible = fields.Selection([('yes', 'Visible'), ('no', 'No visible'), ('all', 'Todos')], string ="Visible en web", default='all')
    stock_available = fields.Selection([('yes', 'Disponible'), ('no', 'No disponible'), ('all', 'Todos')], string ="Available stock", default='all')
    search_text = fields.Char("Search text")
    offset = fields.Integer("Start", default=0)
    limit = fields.Integer("Limit", default=0)
    date = fields.Date()
    stock_field = fields.Selection(
        (('qty_available', 'Available'), ('web_global_stock', 'Web global stock')), default='web_global_stock')
    valued = fields.Boolean()
    location_ids = fields.Many2many('stock.location', 'locations')

    @api.multi
    def open_product_web_report(self):
        self.ensure_one()
        domain = [('type', '!=', 'service')]
        prod_ctx = self.env['product.product']
        if self.date:
            use_date = self.date
            if self.location_ids:
                prod_ctx = self.env['product.product'].with_context(to_date=self.date, location=self.location_ids._ids)
            else:
                prod_ctx = self.env['product.product'].with_context(to_date=self.date)
        else:
            use_date = date.today().strftime('%Y-%m-%d')
        offset = 0
        limit = 50000
        if self.web_visible == 'yes':
            domain.append(['web','=',True])
        elif self.web_visible == 'no':
            domain.append(['web', '=', False])

        if self.stock_available == 'yes':
            domain.append(['web_global_stock', '>', 0])
        elif self.stock_available == 'no':
            domain.append(['web_global_stock', '<=', 0])

        if self.search_text:
            domain.append(['tag_names', 'ilike', self.search_text])
            domain.append(['display_name', 'ilike', self.search_text])

        if self.offset:
            offset = self.offset
        if self.limit:
            limit = self.limit
        else:
            limit = prod_ctx.search(domain, count=True)

        fields = ('display_name', 'default_code', 'tag_names', 'web', self.stock_field)
        read = []
        inc = 250
        print "Numero de registros a exportar: %s\nBuscando ..."%limit
        while offset <= limit:
            print "Recuperando %s de %s"%(offset, limit)

            product_dict = prod_ctx.search_read(domain, fields, offset=offset, limit=inc)
            new_dict = {x.pop('id'): x for x in product_dict}
            if self.valued:
                self.env.cr.execute("""SELECT product_id,
                    SUM(quantity) AS CantidadTotal, SUM(price_subtotal) AS ImporteTotal,
                    AVG(arancel) AS Arancel,
                    CASE
                        WHEN SUM(quantity) = 0 THEN NULL
                        ELSE SUM(price_subtotal)/SUM(quantity)

                    END AS PrecioUnitario,
                    CASE
                        WHEN AVG(quantity) = 0 THEN NULL
                        WHEN AVG(price_subtotal) = 0 THEN NULL
                        ELSE ROUND(CAST((AVG(arancel) / (AVG(price_subtotal)/AVG(quantity))) * 100 AS numeric), 2)

                    END AS PorcentajeArancel,
                    AVG(delivery) as delivery, AVG(price_unit) as price_unit

                FROM(

                    SELECT *
                    FROM(
                        SELECT ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY date_invoice DESC) AS ordered, *
                        FROM(
                            SELECT ai.date_invoice, il.product_id, il.quantity, il.price_subtotal, il.arancel_percentage, il.arancel,
                            CASE
                                WHEN ai.amount_untaxed = 0 THEN NULL
                                WHEN il.quantity = 0 THEN NULL
                                ELSE ((il.price_subtotal / ai.amount_untaxed) * ai.delivery_cost) / il.quantity
                            END AS delivery,
                             il.price_unit as price_unit
                            FROM account_invoice_line il
                                JOIN product_product pp ON il.product_id = pp.id
                                JOIN account_invoice ai ON il.invoice_id = ai.id
                                JOIN res_partner rp ON ai.partner_id = rp.id
                                JOIN res_country rc ON rp.country_id = rc.id
                            WHERE pp.default_code != 'LM' 
                                and pp.id in %s and ai.date_invoice <= '%s'
                                and ai.company_id = %s
                                and ai.type = 'in_invoice') as tb
                    ) tb2
                    WHERE tb2.ordered <= 3

                )tb3
                GROUP BY product_id
                ORDER BY product_id""" % (tuple(new_dict.keys()), use_date, self.env.user.company_id.id))
                aranceles = self.env.cr.fetchall()
                for arancel in aranceles:
                    new_dict[arancel[0]].update(
                        {'cantidad_total': arancel[1],
                         'importe_total': arancel[2], 'arancel': arancel[3],
                         'precio_unitario': arancel[4],
                         'porcentaje_arancel': arancel[5],
                         'delivery': arancel[6],
                         'price_unit': arancel[7]})
            read.extend(new_dict.values())
            offset += inc
        print "Generando XLS ..."
        #product['ids'] = self.env['product.product'].search(domain).ids
        return {'type': 'ir.actions.report.xml',
                'report_name': 'product_web_xls',
                'datas': {'form': read, 'stock_field': self.stock_field, 'valued': self.valued}}
