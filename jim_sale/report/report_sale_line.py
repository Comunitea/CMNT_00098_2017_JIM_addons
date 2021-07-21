# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class ReportSaleLineJim(models.Model):
    _name = "report.sale.line.jim"
    _description = "Sales Lines Orders Statistics"
    _auto = False
    _rec_name = "order_line_id"
    _order = "order_line_id"

    order_line_id = fields.Many2one("sale.order.line", readonly=True)
    product_id = fields.Many2one(
        "product.product", string="Articulo", readonly=True
    )
    product_code = fields.Char(string="Referencia", readonly=True)
    template_code = fields.Char(string="Ref (patrón)", readonly=True)
    qty_delivered = fields.Float(string="Entregada", readonly=True)
    qty_invoiced = fields.Float(string="Facturada", readonly=True)
    product_uom_qty = fields.Float(string="Pedida", readonly=True)
    price_subtotal = fields.Monetary(string="Subtotal", readonly=True)
    price_unit = fields.Float(string="Precio", readonly=True)
    currency_id = fields.Many2one(related="order_line_id.currency_id")
    partner_id = fields.Many2one(
        "res.partner", string="Cliente", readonly=True
    )
    user_id = fields.Many2one("res.users", string="Comercial", readonly=True)
    order_id = fields.Many2one("sale.order", string="Order", readonly=True)
    company_id = fields.Many2one(
        "res.company", string="Company", readonly=True
    )

    # picking_id = fields.Many2one('stock.picking', readonly=True)
    line_delivered_state = fields.Selection(
        [("E", "Entregado"), ("NE", "No entregado")], "Entrega", readonly=True
    )
    line_invoice_state = fields.Selection(
        [("NF1", "No fact 100%"), ("F", "Facturado"), ("NF", "No facturado")],
        "Factura",
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("proforma", "Proforma"),
            ("lqdr", "Pending LQDR"),
            ("progress_lqdr", "Progress LQDR"),
            ("pending", "Revision Pending"),
            ("progress", "Confirm in Progress"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ]
    )
    date = fields.Datetime(string="Fecha", readonly=True)
    #TODO: Migrar, no existe el modelo product.attribute.value
    # ~ color_id = fields.Many2one(
        # ~ "product.attribute.value", "Color", readonly=True
    # ~ )
    # ~ size_id = fields.Many2one("product.attribute.value", "Size", readonly=True)

    def _select(self):
        select_str = """
             SELECT l.id as id,
                    l.id as order_line_id,
                    l.product_id as product_id,
                    l.price_subtotal,
                    l.price_unit,
                    l.qty_delivered,
                    l.qty_invoiced,
                    l.product_uom_qty,
                    l.company_id,
                    pp.default_code as product_code,
                    pt.default_code as template_code,
                    so.partner_id as partner_id,
                    so.state as state,
                    so.user_id as user_id,
                    so.date_order as date,
                    so.id as order_id,

                    CASE WHEN l.qty_delivered > 0
                        THEN 'E'
                        ELSE 'NE'
                    END as line_delivered_state,
                    CASE
                        WHEN l.qty_invoiced = 0 THEN 'NF'
                        WHEN l.qty_to_invoice = qty_delivered THEN 'F'
                        ELSE 'NF1'
                    END as line_invoice_state"""
                    #TODO: Migrar, no existe el modelo product.attribute.value
                    # ~ ,
                     # ~ (SELECT pav.id FROM product_attribute_value pav INNER JOIN product_attribute_value_product_product_rel pavppr
                                # ~ on pavppr.product_attribute_value_id = pav.id
                                # ~ INNER JOIN  product_attribute pa on pav.attribute_id = pa.id
                                # ~ WHERE pavppr.product_product_id = product_id and pa.is_color = True LIMIT 1)
                        # ~ as color_id,
                            # ~ (SELECT pav.id FROM product_attribute_value pav INNER JOIN product_attribute_value_product_product_rel pavppr
                                # ~ on pavppr.product_attribute_value_id = pav.id
                                # ~ INNER JOIN  product_attribute pa on pav.attribute_id = pa.id
                                # ~ WHERE pavppr.product_product_id = product_id and pa.is_color = False LIMIT 1)
                        # ~ as size_id

        # ~ """
        return select_str

    def _from(self):
        from_str = """sale_order_line l
                        left join sale_order so on l.order_id = so.id
                        left join product_product pp on pp.id = l.product_id
                        left join product_template pt on pp.product_tmpl_id = pt.id"""
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                    l.id,
                    l.product_id,
                    pp.default_code,
                    pt.default_code,
                    so.partner_id,
                    so.state,
                    so.user_id,
                    so.date_order,
                    so.id"""
                    #TODO: Migrar, no existe el modelo product.attribute.value
                    # ~ ,
                    # ~ color_id,
                    # ~ size_id


        # ~ """
        return group_by_str

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """CREATE or REPLACE VIEW %s as (
            %s
            FROM %s
            %s
            )"""
            % (self._table, self._select(), self._from(), self._group_by())
        )
