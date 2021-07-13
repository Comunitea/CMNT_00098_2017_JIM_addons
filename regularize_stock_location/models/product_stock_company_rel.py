# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api, tools


class ProductStockComapnyRel(models.Model):

    _name = "product.stock.company.rel"
    _description = "Stock por compañia de articulos"
    _auto = False
    _rec_name = "id"
    _order = "id"

    product_company_id = fields.Many2one(
        "res.company", string="Product Company"
    )
    stock_company_id = fields.Many2one("res.company", string="Stock Company")
    location_id = fields.Many2one("stock.location", "Orig location")
    product_id = fields.Many2one("product.product")
    qty = fields.Float("Qty")
    bool_company_id = fields.Boolean("Same company")

    def _select(self):
        select_str = """
        select 
         row_number() OVER () AS id,        
        sq.product_id as product_id,
        sum(sq.qty) as qty,
        min(pt.company_id) as product_company_id,
        sq.company_id as stock_company_id,
        sq.location_id as location_id,
        (sq.company_id = min(pt.company_id)) as bool_company_id 
         """

        return select_str

    def _from(self):
        from_str = """
       stock_quant sq 
        join product_product pp on pp.id = sq.product_id
        join product_template pt on pt.id = pp.product_tmpl_id
        
        group by sq.product_id, sq.company_id, sq.location_id
        order by sq.product_id
        """
        return from_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as (%s FROM %s)""" % (
            self._table,
            self._select(),
            self._from(),
        )
        self.env.cr.execute(sql)
