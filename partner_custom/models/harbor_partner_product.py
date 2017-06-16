# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo import tools

class HarborPartnerProduct(models.Model):

    _name = "harbor.partner.product"
    _auto = False
    _description = "List products, by partner and harbor"

    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product')
    harbor_id = fields.Many2one('res.harbor', string="Harbor")
    product_name = fields.Char("Product name")
    default_code = fields.Char("Internal Ref")

    def _select(self):
        select_str = "SELECT " \
                     "row_number() OVER () AS id," \
                     "rp.id as partner_id, " \
                     "rh.id as harbor_id,  " \
                     "pt.id as product_tmpl_id, " \
                     "pt.default_code as default_code, " \
                     "pt.name as product_name "
        return select_str

    def _from (self):
        from_str ="res_harbor_res_partner_rel rhrpr " \
                    "left join res_partner rp on rhrpr.res_partner_id = rp.id " \
                    "join product_supplierinfo spi on spi.name = rhrpr.res_partner_id " \
                    "left join product_template pt on pt.id = spi.product_tmpl_id " \
                    "left join res_harbor rh on rh.id = rhrpr.res_harbor_id"
        return from_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'harbor_partner_product')
        self._cr.execute("""CREATE or REPLACE VIEW  harbor_partner_product as (
            %s
            FROM (
                %s)
                )""" % (self._select(),
                        self._from()
                        ))


