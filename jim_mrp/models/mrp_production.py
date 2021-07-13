# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


STOCK_TO_REFRESH = "global_real_stock"


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    @api.model
    def _get_default_picking_type(self):
        domain_wh = [
            ("partner_id", "=", self.env.user.company_id.partner_id.id)
        ]
        warehouse_id = self.env["stock.warehouse"].search(domain_wh, limit=1)
        types = warehouse_id and warehouse_id.manu_type_id
        if not types:
            return super(MrpProduction, self)._get_default_picking_type()
        return types[:1]

    global_real_stock = fields.Float(
        "Global Real Stock",
        digits=dp.get_precision("Product Unit of Measure"),
        help="Real stock in all companies.",
    )
    web_global_stock = fields.Float(
        "Web stock",
        readonly=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    note = fields.Text()

    @api.multi
    def refresh_stock(self):
        for production in self:
            production.global_real_stock = (
                production.product_id.global_real_stock
            )
            production.web_global_stock = (
                production.product_id.web_global_stock
            )
            for line in production.move_raw_ids:
                line.global_real_stock = line.product_id.global_real_stock
                line.web_global_stock = line.product_id.web_global_stock

    @api.onchange("product_id")
    def refresh_stock_product_id(self):
        if self.product_id:
            self.global_real_stock = self.product_id.global_real_stock
            self.web_global_stock = self.product_id.web_global_stock

    @api.onchange("bom_id")
    def refresh_stock_bom_id(self):
        for line in self.move_raw_ids:
            line.global_real_stock = line.product_id.global_real_stock
            line.web_global_stock = line.product_id.web_global_stock

    @api.model
    def create(self, values):
        res = super(MrpProduction, self).create(values)
        if values.get("product_id"):
            ctx = dict(self._context)
            ctx.pop("force_company", False)
            res.with_context(ctx).refresh_stock()
        return res

    @api.multi
    def set_done_production(self):
        ctx = self._context.copy()

        for production in self.filtered(lambda x: x.state == "confirmed"):
            if production.availability != "assigned":
                production.action_assign()
            if production.availability == "assigned":
                ctx.update(active_id=production.id)
                new_wzd = (
                    self.env["mrp.product.produce"]
                    .with_context(ctx)
                    .create({})
                )
                new_wzd.do_produce()

        for production in self.filtered(lambda x: x.state == "progress"):
            production.button_mark_done()


class StockMove(models.Model):
    _inherit = "stock.move"

    global_real_stock = fields.Float(
        "Global Real Stock",
        digits=dp.get_precision("Product Unit of Measure"),
        help="Real stock in all companies.",
    )
    web_global_stock = fields.Float(
        "Web stock",
        readonly=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )


class MrpBoom(models.Model):
    _inherit = "mrp.bom"

    @api.constrains("product_id", "product_tmpl_id", "bom_line_ids")
    def _check_product_recursion(self):
        for bom in self:
            if bom.product_id:
                if bom.bom_line_ids.filtered(
                    lambda x: x.product_id == bom.product_id
                ):
                    raise ValidationError(
                        _(
                            "BoM line product %s should not \
be same as BoM product."
                        )
                        % bom.display_name
                    )
            else:
                return super(MrpBoom, self)._check_product_recursion()
