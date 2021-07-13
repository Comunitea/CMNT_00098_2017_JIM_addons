# Copyright 2017 Javier Colmenero, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class AccImportFiles(models.TransientModel):
    _name = "acc.import.files"

    @api.multi
    def acc_import_files(self):
        self.ensure_one()
        self.env["a3.import.log"].sudo().import_files()
