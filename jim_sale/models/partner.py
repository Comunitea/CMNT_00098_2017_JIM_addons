# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from lxml import etree
from odoo.exceptions import ValidationError


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):

        res = super(ResPartner, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )
        if self._context.get("no_edit", False):
            arch = res["arch"]
            doc = etree.fromstring(arch)
            form_node = doc.xpath("//form")
            if form_node:
                form_node[0].set("edit", "false")
                fields_node = doc.xpath("//field")
                for field in fields_node:
                    modif = field.attrib["modifiers"][1:-1]
                    if modif == "":
                        modif = '"readonly": true'
                    else:
                        modif += ',"readonly": true'
                    field.attrib["modifiers"] = "{" + modif + "}"

                self.tostring = etree.tostring(doc)
                res["arch"] = self.tostring
        return res

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        res.check_state_id()
        return res

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        for partner in self:
            partner.check_state_id()
        return res

    @api.multi
    def check_state_id(self):

        for partner in self:
            if (
                partner.country_id
                and partner.country_id.id == 69
                and not partner.state_id
            ):
                raise ValidationError(
                    "No puedes tener un contacto sin provincia de envío. Partner con id: %s"
                    % partner.id
                )
