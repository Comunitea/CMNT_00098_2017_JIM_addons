# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, tools


class ReportStockForecat(models.Model):
    _inherit = "report.stock.forecast"

    location_id = fields.Many2one("stock.location", "Location", readonly=True)
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    out_qty = fields.Float(readonly=True, string="Outgoing qty")
    in_qty = fields.Float(readonly=True, string="Incoming qty")
    real_qty = fields.Float(readonly=True, string="Real qty")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, "report_stock_forecast")
        self._cr.execute(
            """CREATE or REPLACE VIEW report_stock_forecast AS (SELECT
        MIN(id) as id,
        product_id as product_id,
        date as date,
        sum(product_qty) AS quantity,
        sum(sum(product_qty)) OVER (PARTITION BY product_id ORDER BY date) AS cumulative_quantity,
        location_id as location_id,
        company_id as company_id,
        sum(real_qty) as real_qty,
        sum(in_qty) as in_qty,
        sum(out_qty) as out_qty
        FROM
        (SELECT
        MIN(id) as id,
        MAIN.product_id as product_id,
        SUB.date as date,
        MAIN.location_id as location_id,
        MAIN.company_id as company_id,
        sum(MAIN.real_qty)as real_qty,
        sum(MAIN.in_qty)as in_qty,
        sum(MAIN.out_qty) as out_qty,
        CASE WHEN MAIN.date = SUB.date THEN sum(MAIN.product_qty) ELSE 0 END as product_qty
        FROM
        (SELECT
            MIN(sq.id) as id,
            sq.product_id,
            date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) as date,
            SUM(sq.qty) AS product_qty,
            sq.location_id,
            sq.company_id,
            SUM(sq.qty) AS real_qty,
            SUM(0.0) as in_qty,
            SUM(0.0) as out_qty
            FROM
            stock_quant as sq
            LEFT JOIN
            product_product ON product_product.id = sq.product_id
            LEFT JOIN
            stock_location location_id ON sq.location_id = location_id.id
            WHERE
            location_id.usage = 'internal'
            GROUP BY date, sq.product_id, sq.location_id, sq.company_id
            UNION ALL
            SELECT
            MIN(-sm.id) as id,
            sm.product_id,
            CASE WHEN sm.date_expected > CURRENT_DATE
            THEN date_trunc('week', to_date(to_char(sm.date_expected, 'YYYY/MM/DD'), 'YYYY/MM/DD'))
            ELSE date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) END
            AS date,
            SUM(sm.product_qty) AS product_qty,
            sm.location_dest_id,
            sm.company_id,
            SUM(0.0) AS real_qty,
            SUM(sm.product_qty) AS in_qty,
            SUM(0.0) AS out_qty
            FROM
               stock_move as sm
            LEFT JOIN
               product_product ON product_product.id = sm.product_id
            LEFT JOIN
            stock_location dest_location ON sm.location_dest_id = dest_location.id
            LEFT JOIN
            stock_location source_location ON sm.location_id = source_location.id
            WHERE
            sm.state IN ('confirmed','assigned','waiting') and
            source_location.usage != 'internal' and dest_location.usage = 'internal'
            GROUP BY sm.date_expected,sm.product_id, sm.location_dest_id, sm.company_id
            UNION ALL
            SELECT
                MIN(-sm.id) as id,
                sm.product_id,
                CASE WHEN sm.date_expected > CURRENT_DATE
                    THEN date_trunc('week', to_date(to_char(sm.date_expected, 'YYYY/MM/DD'), 'YYYY/MM/DD'))
                    ELSE date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) END
                AS date,
                SUM(-(sm.product_qty)) AS product_qty,
                sm.location_id,
                sm.company_id,
                SUM(0.0) AS real_qty,
                SUM(0.0) AS in_qty,
                SUM(sm.product_qty) AS out_qty
            FROM
               stock_move as sm
            LEFT JOIN
               product_product ON product_product.id = sm.product_id
            LEFT JOIN
               stock_location source_location ON sm.location_id = source_location.id
            LEFT JOIN
               stock_location dest_location ON sm.location_dest_id = dest_location.id
            WHERE
                sm.state IN ('confirmed','assigned','waiting') and
            source_location.usage = 'internal' and dest_location.usage != 'internal'
            GROUP BY sm.date_expected,sm.product_id, sm.location_id, sm.company_id
            UNION ALL
            SELECT
                MIN(-sol.id) as id,
                sol.product_id,
                CASE WHEN sale_order.requested_date is not null and sale_order.requested_date > CURRENT_DATE
                    THEN date_trunc('week', to_date(to_char(sale_order.requested_date, 'YYYY/MM/DD'), 'YYYY/MM/DD'))
                    ELSE date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) END,
                SUM(-(sol.product_uom_qty)) AS product_qty,
                procurement_rule.location_src_id as location_id,
                sale_order.company_id as company_id,
                SUM(0.0) AS real_qty,
                SUM(0.0) AS in_qty,
                SUM(sol.product_uom_qty) AS out_qty
                FROM
                   sale_order_line as sol
                LEFT JOIN
                   product_product ON product_product.id = sol.product_id
                LEFT JOIN
                sale_order ON sale_order.id = sol.order_id
                LEFT JOIN
                stock_location_route ON stock_location_route.id = sol.route_id
                LEFT JOIN
                procurement_rule ON procurement_rule.route_id = stock_location_route.id
            WHERE
                sol.state IN ('lqdr','pending')
            GROUP BY sol.product_id, procurement_rule.location_src_id, sale_order.company_id,sale_order.requested_date
            )
         as MAIN
     LEFT JOIN
     (SELECT DISTINCT date
      FROM
      (
             SELECT date_trunc('week', CURRENT_DATE) AS DATE
             UNION ALL
             SELECT date_trunc('week', to_date(to_char(sm.date_expected, 'YYYY/MM/DD'), 'YYYY/MM/DD')) AS date
             FROM stock_move sm
             LEFT JOIN
             stock_location source_location ON sm.location_id = source_location.id
             LEFT JOIN
             stock_location dest_location ON sm.location_dest_id = dest_location.id
             WHERE
             sm.state IN ('confirmed','assigned','waiting') and sm.date_expected > CURRENT_DATE and
             ((dest_location.usage = 'internal' AND source_location.usage != 'internal')
              or (source_location.usage = 'internal' AND dest_location.usage != 'internal'))) AS DATE_SEARCH)
             SUB ON (SUB.date IS NOT NULL)
    GROUP BY MAIN.product_id,SUB.date, MAIN.date, MAIN.location_id, MAIN.company_id
    ) AS FINAL
    GROUP BY product_id,date,location_id, company_id)"""
        )
