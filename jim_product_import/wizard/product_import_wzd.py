# © 2018 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, _
from odoo.exceptions import UserError
import xlrd
import xlwt
import base64

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import (
    serialize_exception,
    content_disposition,
)
from io import StringIO
import logging

_logger = logging.getLogger(__name__)

# Global variable to store the new created templates
template_ids = []


class Binary(http.Controller):
    @http.route("/web/binary/download_document", type="http", auth="public")
    @serialize_exception
    def download_document(self, filename, filecontent, **kw):
        # print base64.b64decode(filecontent)
        return request.make_response(
            filecontent,
            [
                ("Content-Type", "application/octet-stream"),
                ("Content-Disposition", content_disposition(filename)),
            ],
        )
        file = base64.b64decode(self.import_file)
        book = xlrd.open_workbook(filename)
        sh = book.sheet_by_index(0)
        filecontent = []
        stream = StringIO.StringIO()
        for nline in range(0, sh.nrows):
            filecontent.append(sh.row_values(nline))

        print(filecontent)
        if not filecontent:
            return request.not_found()
        else:
            return request.make_response(
                filecontent,
                [
                    ("Content-Type", "application/octet-stream"),
                    ("Content-Disposition", content_disposition(filename)),
                ],
            )


class ProductImportWzd(models.TransientModel):
    _name = "product.import.wzd"

    name = fields.Char("Importation name")
    file = fields.Binary(string="File")
    brand_id = fields.Many2one("product.brand", "Brand")
    filename = fields.Char(string="Filename")
    categ_id = fields.Many2one("product.category", "Default product category")
    create_attributes = fields.Boolean("Create attributes/values if neccesary")

    def _parse_row_vals(self, row, idx):
        res = {
            "default_code": row[0],
            "x_barcode": row[1],
            "barcode": row[3],
            "ext_id": row[4],
        }

        # Check mandatory values setted
        return res

    def get_ref(self, ext_id):
        ext_id_c = ext_id.split(".")
        if len(ext_id_c) == 1:
            domain = [
                ("model", "=", "product.product"),
                ("module", "=", ""),
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

    def import_products(self):
        self.ensure_one()
        _logger.info(_("STARTING PRODUCT IMPORTATION"))

        # get the first worksheet
        file = base64.b64decode(self.file)

        book = xlrd.open_workbook(file_contents=file)
        sh = book.sheet_by_index(0)
        created_product_ids = []
        idx = 1
        error_idx = 0
        p_ids = []
        row_err = []
        stream = StringIO.StringIO()
        workbook = xlwt.Workbook(encoding="ascii")
        worksheet = workbook.add_sheet("Lista de filas con error")
        for nline in range(1, sh.nrows):
            if idx < 15000:
                idx += 1
                row = sh.row_values(nline)
                row_vals = self._parse_row_vals(row, idx)
                res_id = self.get_ref(row_vals["ext_id"])
                if res_id:
                    sql = "update product_product set barcode='{}' where id={}".format(
                        str(row_vals["barcode"]), res_id
                    )
                    print(sql)
                    self._cr.execute(sql)
                    p_ids.append(res_id)
                    _logger.info(
                        _(
                            "Van {} de {}: Update {} a {}".format(
                                nline, sh.nrows, res_id, row_vals["barcode"]
                            )
                        )
                    )
                else:
                    colu = 0
                    for col in row_vals:

                        row_err.append(row_vals[col])
                        worksheet.write(error_idx, colu, label=row_vals[col])
                        colu += 1
                    error_idx += 1
                    _logger.info(
                        _(
                            "Error en {} a {}".format(
                                row_vals["ext_id"], row_vals["barcode"]
                            )
                        )
                    )

        workbook.save("../../var/log/mecalux/Errores.xls")
        return
        workbook.save(stream)
        stream.seek(0)
        data = stream.read()
        return {
            "type": "ir.actions.act_url",
            "url": "/web/binary/download_document?filename=./Errores.xls&filecontent={}".format(
                data
            ),
            "target": "self",
        }

    def action_view_products(self, product_ids):
        self.ensure_one()
        action = self.env.ref("product.product_normal_action").read()[0]
        action["domain"] = [("id", "in", product_ids)]
        return action
