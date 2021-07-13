# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class ShippingContainerType(models.Model):

    _name = "shipping.container.type"

    name = fields.Char("Container type", required=True)
    volume = fields.Float(
        "Volumen", help="Container volume (m3)", required=True
    )
    length = fields.Float("Length", help="Length(m)")
    height = fields.Float("Height", help="Height(m)")
    width = fields.Float("Width", help="Width(m)")

    @api.onchange("length", "height", "width")
    def onchange_dimensions(self):
        if self.length and self.height and self.width:
            self.volume = self.length * self.height * self.width


class ShippingContainer(models.Model):

    _name = "shipping.container"

    @api.one
    def _get_moves(self):
        self.move_ids_count = len(self.move_ids)

    @api.one
    def _get_partners(self):
        self.partner_ids = self.picking_ids.partner_id

    @api.multi
    def _available_volume(self):
        for container in self:
            volume = container.shipping_container_type_id.volume
            weight = 0.00
            for move in container.move_ids:
                volume -= move.product_id.volume * move.product_uom_qty
                weight += move.product_id.weight * move.product_uom_qty
            container.available_volume = volume
            container.weight = weight

    name = fields.Char("Container Ref.", required=True)
    date_expected = fields.Date("Date expected", required=True)
    date_shipment = fields.Date("Shipment date")
    picking_ids = fields.One2many(
        "stock.picking", "shipping_container_id", "Pickings"
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "shipping.container"
        ),
    )
    harbor_id = fields.Many2one("res.harbor", string="Harbor", required=True)
    move_ids = fields.One2many(
        "stock.move", "shipping_container_id", string="Moves"
    )
    move_ids_count = fields.Integer("Move ids count", compute="_get_moves")
    harbor_dest_id = fields.Many2one("res.harbor", string="Dest. harbor")

    state = fields.Selection(
        [
            ("loading", "Loading"),
            ("transit", "Transit"),
            ("destination", "Destination"),
        ],
        default="loading",
    )
    shipping_container_type_id = fields.Many2one(
        "shipping.container.type", "Type"
    )
    available_volume = fields.Float(
        "Available volume (m3)", compute="_available_volume"
    )
    weight = fields.Float("Weight (kgr.)", compute="_available_volume")
    incoterm_id = fields.Many2one("stock.incoterms", string="Incoterm")

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Container name must be unique")
    ]

    @api.multi
    def action_view_move_ids(self):
        action = self.env.ref(
            "shipping_container.container_picking_tree_action"
        ).read()[0]
        action["domain"] = [("id", "in", self.move_ids.ids)]
        return action

    def set_transit(self):
        self.state = "transit"

    def set_destination(self):
        self.state = "destination"

    def set_loading(self):
        self.state = "loading"

    @api.multi
    def write(self, vals):
        if vals.get("date_expected", False):
            for container in self:
                if vals["date_expected"] != container.date_expected:
                    for pick in container.picking_ids:
                        pick.min_date = vals["date_expected"]
        return super(ShippingContainer, self).write(vals)
