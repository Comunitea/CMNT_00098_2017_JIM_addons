# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class PickingManageVariant(models.TransientModel):
    _name = "picking.manage.variant"

    product_tmpl_id = fields.Many2one(
        comodel_name="product.template", string="Template", required=True
    )
    variant_line_ids = fields.Many2many(
        comodel_name="picking.manage.variant.line", string="Variant Lines"
    )

    def onchange(self, values, field_name, field_onchange):  # pragma: no cover
        if "variant_line_ids" in field_onchange:
            for sub in (
                "product_id",
                "disabled",
                "value_x",
                "value_y",
                "product_qty",
            ):
                field_onchange.setdefault("variant_line_ids." + sub, u"")
        return super(PickingManageVariant, self).onchange(
            values, field_name, field_onchange
        )

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):

        self.variant_line_ids = [(6, 0, [])]
        template = self.product_tmpl_id
        context = self.env.context
        record = self.env[context["active_model"]].browse(context["active_id"])
        if context["active_model"] == "stock.move":
            stock_picking = record.picking_id
        else:
            stock_picking = record
        num_attrs = len(template.attribute_line_ids)
        if not template or not num_attrs:
            return
        line_x = template.attribute_line_ids[0]
        line_y = False if num_attrs == 1 else template.attribute_line_ids[1]
        lines = []
        for value_x in line_x.value_ids:
            for value_y in line_y and line_y.value_ids or [False]:
                # Filter the corresponding product for that values
                values = value_x
                if value_y:
                    values += value_y
                product = template.product_variant_ids.filtered(
                    lambda x: not (values - x.product_template_attribute_value_ids)
                )[:1]
                move_line = stock_picking.move_lines.filtered(
                    lambda x: x.product_id == product
                )[:1]
                lines.append(
                    (
                        0,
                        0,
                        {
                            "product_id": product,
                            "disabled": not bool(product),
                            "value_x": value_x,
                            "value_y": value_y,
                            "product_qty": move_line.product_qty,
                        },
                    )
                )
        self.variant_line_ids = lines

    def button_transfer_to_order(self):
        context = self.env.context
        record = self.env[context["active_model"]].browse(context["active_id"])
        if context["active_model"] == "stock.move":
            stock_picking = record.picking_id
        else:
            stock_picking = record
        MoveLine = self.env["stock.move"]
        lines2unlink = MoveLine
        for line in self.variant_line_ids:
            stock_move = stock_picking.move_lines.filtered(
                lambda x: x.product_id == line.product_id
            )
            if stock_move:
                if not line.product_qty:
                    # Done this way because there's a side effect removing here
                    lines2unlink |= stock_move
                else:
                    stock_move.product_qty = line.product_qty
            elif line.product_qty:
                move_line = MoveLine.new(
                    {
                        "product_id": line.product_id.id,
                        "product_uom": line.product_id.uom_id,
                        "product_uom_qty": line.product_qty,
                        "picking_id": stock_picking.id,
                        "location_id": stock_picking.location_id.id,
                        "location_dest_id": stock_picking.location_dest_id.id,
                    }
                )
                move_line.onchange_product_id()
                move_line.product_uom_qty = line.product_qty
                order_line_vals = move_line._convert_to_write(move_line._cache)
                stock_picking.move_lines.create(order_line_vals)

        lines2unlink.unlink()


class PickingManageVariantLine(models.TransientModel):
    _name = "picking.manage.variant.line"

    product_id = fields.Many2one(
        comodel_name="product.product", string="Variant", readonly=True
    )
    disabled = fields.Boolean()
    #TODO: Migrar, no existe el modelo product.attribute.value
    # ~ value_x = fields.Many2one(comodel_name="product.attribute.value")
    # ~ value_y = fields.Many2one(comodel_name="product.attribute.value")
    product_qty = fields.Float(
        string="Quantity", digits="Product UoS"
    )
