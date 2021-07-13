# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class ReportSaleLineJimAttributes(models.Model):
    _name = "report.sale.line.jim.attributes"
    _description = "Sale Lines Statistics Attributes"
    _auto = False
    _rec_name = "id"
    _order = "id"

    product_id = fields.Many2one(
        "product.product", string="Articulo", readonly=True
    )
    color = fields.Char(string="Color", readonly=True)
    talla = fields.Char(string="Talla", readonly=True)
    attribute_names = fields.Char(string="Variante", readonly=True)
    product_code = fields.Char(string="Referencia", readonly=True)
    # qty_delivered = fields.Float(string="Entregada", readonly=True)
    # qty_invoiced = fields.Float(string="Facturada", readonly=True)
    product_uom_qty = fields.Float(string="Pedida", readonly=True)
    price_subtotal = fields.Float(string="Subtotal", readonly=True)
    price_unit = fields.Float(string="Precio", readonly=True)
    company_id = fields.Many2one(
        "res.company", string="Company", readonly=True
    )

    # picking_id = fields.Many2one('stock.picking', readonly=True)
    # line_delivered_state = fields.Selection([('E','Entregado'), ('NE','No entregado')], "Entrega", readonly=True)
    # line_invoice_state = fields.Selection([('NF1','No fact 100%'), ('F','Facturado'), ('NF','No facturado')], "Factura", readonly=True)
    # state = fields.Selection([
    #     ('draft', 'Quotation'),
    #     ('sent', 'Quotation Sent'),
    #     ('proforma', 'Proforma'),
    #     ('lqdr', 'Pending LQDR'),
    #     ('progress_lqdr', 'Progress LQDR'),
    #     ('pending', 'Revision Pending'),
    #     ('progress', 'Confirm in Progress'),
    #     ('sale', 'Sales Order'),
    #     ('done', 'Locked'),
    #     ('cancel', 'Cancelled'),
    # ])
    date = fields.Datetime(string="Fecha", readonly=True)

    def _select(self):
        select_str = """            
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    sum(l.price_subtotal) as price_subtotal, 
                    sum(l.price_unit) as price_unit,
                    sum(l.product_uom_qty) as product_uom_qty,
                    l.company_id,
                    pp.default_code as product_code,
                    so.date_order as date,
                    coalesce(nullif(pp.attribute_names,'') , 'Plantilla') as attribute_names, 
                    case when split_part(pp.attribute_names, ', ',1) ilike '%Color%' 
                    then split_part(pp.attribute_names, ', ',1) 
                    else 
                        case when split_part(pp.attribute_names, ', ',2) ilike '%Color%' 
                            then split_part(pp.attribute_names, ', ',2)
                            else 'Sin valor'
                        end
                            end as color,
                    case when split_part(pp.attribute_names, ', ',1) not ilike '%Color%' 
                    then split_part(pp.attribute_names, ', ',1) 
                    else 
                        case when split_part(pp.attribute_names, ', ',2) not ilike '%Color%' 
                            then split_part(pp.attribute_names, ', ',2)
                            else 'Sin Valor'
                        end
                            end as talla
                    
                                    
        """
        return select_str

    def _from(self):
        from_str = """ sale_order_line l
                        left join sale_order so on l.order_id = so.id 
                        left join product_product pp on pp.id = l.product_id
                        """
        return from_str

    def _group_by(self):
        group_by_str = """
            WHERE
                so.state in ('sale', 'done') and l.id > 400000
            GROUP BY 
                   l.product_id,
                    l.company_id,
                    pp.display_name,
                    pp.default_code,
                    pp.attribute_names,
                    so.date_order
                    
                    
        """
        return group_by_str

    @api.model_cr
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
