# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta
import sga_file
import os
import re



class StockPickingType(models.Model):

    _inherit = "stock.picking.type"
    company_sequence_id = sequence_id = fields.Many2one('ir.sequence', 'Reference Sequence (Company)')
