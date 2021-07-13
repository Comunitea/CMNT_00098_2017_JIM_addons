# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ContainerPickingLineWizard(models.TransientModel):

    _name = "container.picking.line.wizard"
    _rec_name = "picking_id"

    selected = fields.Boolean("Selected")
    picking_id = fields.Many2one("stock.picking")
    picking_volume = fields.Float("Volume")
    picking_weight = fields.Float("Weight")
    origin = fields.Char("Origin")
    container_id = fields.Many2one(related="picking_id.shipping_container_id")
    container_picking_wzd_id = fields.Many2one("container.picking.wizard")


class ContainerPickingWizard(models.TransientModel):

    _name = "container.picking.wizard"

    name = fields.Char("Name")
    shipping_container_id = fields.Many2one(
        "shipping.container", string="Container"
    )
    line_ids = fields.One2many(
        "container.picking.line.wizard", "container_picking_wzd_id"
    )
    volume = fields.Float("Volume")
    available_volume = fields.Float(
        "Available volume (m3)", compute="_available"
    )
    weight = fields.Float("Weight (kgr.)", compute="_available")

    @api.depends("line_ids.selected")
    def _available(self):
        available_volumen = self.volume
        weight = 0.00
        for line in self.line_ids.filtered(lambda x: x.selected):
            available_volumen -= line.picking_volume
            weight += line.picking_weight
        self.available_volume = available_volumen
        self.weight = weight

    def add_to_container(self):

        if not self.shipping_container_id:
            raise ValidationError(_("No container selected"))
        for line_wz in self.line_ids.filtered(lambda x: x.selected):
            line_wz.picking_id.shipping_container_id = (
                self.shipping_container_id
            )
            line_wz.picking_id.min_date = (
                self.shipping_container_id.date_expected
            )

        for line_wz in self.line_ids.filtered(
            lambda x: not x.selected
            and x.container_id == self.shipping_container_id
        ):
            line_wz.picking_id.shipping_container_id = False
            # line_wz.picking_id.min_date = False

        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "shipping.container",
            "type": "ir.actions.act_window",
            "res_id": self.shipping_container_id.id,
            "context": self.env.context,
        }

    @api.model
    def default_get(self, fields):
        res = super(ContainerPickingWizard, self).default_get(fields)
        shipping_container_id = self.env.context.get("active_id", False)
        if not shipping_container_id:
            return res
        container = self.env["shipping.container"].browse(
            shipping_container_id
        )
        if container.state != "loading":
            raise ValidationError(_('Container not in "loading" state'))
        lines = []
        res["shipping_container_id"] = container.id
        res["name"] = container.name
        res["volume"] = container.shipping_container_type_id.volume
        res["available_volume"] = res["volume"]
        res["weight"] = 0.00
        domain = [
            "|",
            ("harbor_id", "=", False),
            ("harbor_id", "=", container.harbor_id.id),
            ("state", "=", "assigned"),
            ("picking_type_id.code", "=", "incoming"),
        ]

        picking_ids = self.env["stock.picking"].search(domain)
        for pick in picking_ids:
            if pick.shipping_container_id == container:
                selected = True
                res["available_volume"] -= pick.shipping_volume
                res["weight"] += pick.shipping_weight
            else:
                selected = False
            lines.append(
                {
                    "picking_id": pick.id,
                    "selected": selected,
                    "picking_volume": pick.shipping_volume,
                    "picking_weight": pick.shipping_weight,
                    "origin": pick.origin,
                    "container_id": pick.shipping_container_id.id,
                }
            )

        res["line_ids"] = map(lambda x: (0, 0, x), lines)

        return res
