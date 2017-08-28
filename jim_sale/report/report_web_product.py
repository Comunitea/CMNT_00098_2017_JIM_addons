# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class ReportSaleLineJim(models.Model):
    _name = "report.web.product.jim"
    _description = "Productos web"
    _auto = False
    _rec_name = 'product_id'
    _order = 'product_code'

    product_id = fields.Many2one('product.product', string="Artículo", readonly=True)
    template_id = fields.Many2one(related="product_id.product_tmpl_id", string="Plantilla", readonly=True)
    product_code = fields.Char(related='product_id.default_code', string="Ref. artículo", readonly=True)
    tag_id = fields.Many2one('product.tag', string="Etiqueta", readonly=True)
    web = fields.Boolean(related='tag_id.web')

    def _select(self):
        select_str = """
        select 
            row_number() OVER () AS id,
            pp.id as product_id,
            ptag.id as tag_id
        """

        return select_str

    def _from(self):
        from_str = """
                product_product_tag_rel pptr 
                left join product_template pt on pt.id = pptr.tag_id 
                left join product_tag ptag on pptr.product_id = ptag.id 
                left join product_product pp on pp.product_tmpl_id = pt.id
                """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY 
                pp.id,
                ptag.id
        """
        return ""

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))
