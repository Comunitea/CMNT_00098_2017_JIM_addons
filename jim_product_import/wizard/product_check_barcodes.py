# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _
from odoo.exceptions import UserError
import xlrd, xlwt
import base64

import logging

_logger = logging.getLogger(__name__)

# Global variable to store the new created templates
template_ids = []


class ProductCheckBarcodes(models.TransientModel):
    _name = "product.check.barcodes"

    name = fields.Char("Importation name")
    file = fields.Binary(string="File")
    filename = fields.Char(string="Filename")
    categ_id = fields.Many2one("product.category", "Default product category")
    create_attributes = fields.Boolean(
        "Create attributes/values if neccesary", default=False
    )

    def _parse_row_vals(self, row, idx):
        res = {
            "default_code": row[0],
            "name": row[1],
            "old_barcode": row[4],
            "new_barcode": row[3],
        }

        # Check mandatory values setted
        if not row[0]:
            raise UserError(_("Missing default_code in row %s ") % str(idx))
        return res

    def get_ref(self, ext_id):
        ext_id_c = ext_id.split(".")

        if len(ext_id_c) == 1:
            domain = [
                ("model", "=", "product.product"),
                ("module", "=", False),
                ("name", "=", ext_id),
            ]
        else:
            domain = [
                ("model", "=", "product.product"),
                ("module", "=", ext_id_c[0]),
                ("name", "=", ext_id_c[1]),
            ]

        res_id = self.env["ir.model.data"].search(domain, limit=1)
        return res_id and res_id.res_id or False

    def _delete_xml_id(self, res_id, model):
        self._cr.execute(
            "delete from ir_model_data where model = '{}' and res_id = {}".format(
                model, res_id
            )
        )

    def _create_xml_id(self, xml_id, res_id, model):
        virual_module_name = "PT" if model == "product.template" else "PP"
        self._cr.execute(
            "INSERT INTO ir_model_data (module, name, res_id, model) \
            VALUES (%s, %s, %s, %s)",
            (virual_module_name, xml_id, res_id, model),
        )

    def act_barcodes(self, row_vals, idx):

        try:
            default_code = str(int(row_vals["default_code"]))
        except:
            default_code = str(row_vals["default_code"])

        domain = [("default_code", "=", default_code)]
        product = self.env["product.product"].search(domain, limit=1)

        if product:
            # product.message_post("Se ha cambiado el código de barras de {} a {}".format(product.barcode, row_vals['new_barcode'] or default_code ))
            sql = (
                "update product_product set barcode='{}' where id ={}".format(
                    row_vals["new_barcode"], product.id
                )
            )
            self._cr.execute(sql)
        else:
            _logger.info(
                "No se ha encontrado la referencia {} {}".format(
                    default_code, idx
                )
            )
            return False
        return product

    def check_barcodes(self):
        self.ensure_one()
        _logger.info(_("STARTING PRODUCT IMPORTATION"))

        # get the first worksheet
        file = base64.b64decode(self.file)
        book = xlrd.open_workbook(file_contents=file)
        sh = book.sheet_by_index(0)
        created_product_ids = []
        idx = 1
        error_idx = 0
        workbook = xlwt.Workbook(encoding="ascii")
        worksheet = workbook.add_sheet("Lista de filas con error")

        for nline in range(1, sh.nrows):

            idx += 1
            row = sh.row_values(nline)
            row_vals = self._parse_row_vals(row, idx)
            _logger.info(
                _("Evaluando ref %s, %s / %s")
                % (row_vals["default_code"], idx, sh.nrows - 1)
            )

            if row_vals["default_code"] != "" and row_vals["new_barcode"]:
                product = self.act_barcodes(row_vals, idx)
                if product:
                    created_product_ids.append(product.id)
                else:
                    colu = 0
                    for col in row_vals:
                        worksheet.write(error_idx, colu, label=row_vals[col])
                        colu += 1
                    error_idx += 1
        workbook.save("../../var/log/mecalux/Errores_act_barcodes.xls")

        # If existing template, fail, only templates created from this file
        return self.action_view_products(created_product_ids)

    def action_view_products(self, product_ids):
        self.ensure_one()
        action = self.env.ref("product.product_normal_action").read()[0]
        action["domain"] = [("id", "in", product_ids)]
        return action
