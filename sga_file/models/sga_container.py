# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, tools, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import codecs

class SGAContainer(models.Model):

    _name = "sga.container"
    _description = "Mecalux Containers"

    container_number = fields.Char('Container Number')

    @api.model
    def check_container(self, number=False):

        if number:
            domain = [('container_number', '=', number)]
            container_id = self.env['sga.container'].search(domain)
            if container_id:
                return container_id
            else:
                return self.create({'container_number', '=', number})
        else:
            return False

