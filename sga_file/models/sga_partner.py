# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api


SGA_STATE = [
    ("AC", "Actualizado"),
    ("PA", "Pendiente actualizar"),
    ("BA", "Baja"),
    ("ER", "Error"),
]


class ResPartnerSGA(models.Model):
    _inherit = "res.partner"

    # sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
    #                                  ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='F')
    sga_state = fields.Selection(
        SGA_STATE, default="PA", help="Estado integracion con mecalux"
    )

    @api.multi
    def write(self, values):
        fields_to_check = ("ref", "name", "display_name", "is_company")
        fields = sorted(list(set(values).intersection(set(fields_to_check))))
        if fields:
            values.update({"sga_state": "PA"})
        res = super(ResPartnerSGA, self).write(values)
        if fields:
            icp = self.env["ir.config_parameter"]
            if icp.get_param("product_auto"):
                self.new_mecalux_file()
        return res

    @api.model
    def create(self, values):
        res = super(ResPartnerSGA, self).create(values)
        icp = self.env["ir.config_parameter"]
        if icp.get_param("product_auto"):
            res.new_mecalux_file()
        return res

    @api.multi
    def new_mecalux_file(self):
        try:
            ids = [x.id for x in self.filtered(lambda x: x.is_company)]
            ctx = dict(self.env.context)
            ctx["operation"] = "F"
            self.env["sga.file"].with_context(ctx).check_sga_file(
                "res.partner", ids, code="ACC"
            )
            self.write({"sga_state": "AC"})
            return True
        except:
            self.write({"sga_state": "ER"})
            return False
