# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class ReportSaleLineJim(models.Model):
    _name = "report.web.product.jim"
    _description = "Productos web"
    _auto = False
    _rec_name = "product_id"
    _order = "product_code"

    product_id = fields.Many2one(
        "product.product", string="Artículo", readonly=True
    )
    product_code = fields.Char(
        related="product_id.default_code",
        string="Ref. artículo",
        readonly=True,
    )
    tag_names = fields.Char(
        related="product_id.tag_names", string="Etiqueta", readonly=True
    )
    web = fields.Boolean(related="product_id.web")
    web_global_stock = fields.Float(related="product_id.web_global_stock")

    def _select(self):
        select_str = """
        select 
            pp.id as id,
            pp.id as product_id
        """
        return select_str

    def _from(self):
        from_str = """
                product_product pp 
                inner join product_template pt on pt.id = pp.product_tmpl_id
                where pt.type='product'
                """
        return from_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """CREATE or REPLACE VIEW %s as 
        (%s FROM %s)"""
            % (self._table, self._select(), self._from())
        )
