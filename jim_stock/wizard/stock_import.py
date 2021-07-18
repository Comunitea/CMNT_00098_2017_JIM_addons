# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import xlrd
from io import StringIO


class JimStockImport(models.TransientModel):

    _name = "jim.stock.import"

    import_file = fields.Binary("File to import", required=True)
    type = fields.Selection((("in", "In"), ("out", "Out")), required=True)

    def import_stock(self):
        file = base64.b64decode(self.import_file)
        data = xlrd.open_workbook(file_contents=StringIO.StringIO(file).read())
        sh = data.sheet_by_index(0)
        in_out = self.env["stock.in.out"].create({"type": self.type})
        for line in range(1, sh.nrows):
            row = sh.row_values(line)
            if not row[0] or not row[4] or not row[5]:
                continue
            product_code = row[0]
            qty = float(row[5])
            if qty <= 0:
                continue
            product = self.env["product.product"].search(
                [
                    ("default_code", "=", product_code),
                    "|",
                    ("active", "=", True),
                    ("active", "=", False),
                ]
            )
            if not product:
                raise UserError(
                    _("Product with code %s not found") % product_code
                )
            if len(product) > 1:
                raise UserError(
                    _(
                        "Se ha encontrado más de un producto en "
                        "Odoo con "
                        "la referencia %s. Estas referencias "
                        "deben ser únicas"
                    )
                    % product_code
                )

            new_line_vals = {
                "product": product.id,
                "quantity": qty,
                "in_out": in_out.id,
            }
            if self.type == "in":
                location_dest = self.env["stock.location"].search(
                    [("id", "=", row[2])]
                )
                if not location_dest:
                    raise UserError(
                        _("Location with id %s and name %s not found")
                        % row[2],
                        row[3],
                    )
                new_line_vals["location"] = location_dest.id
            if self.type == "out":
                warehouse_code = row[6]
                if warehouse_code:
                    warehouse = self.env["stock.warehouse"].search(
                        [("code", "=", warehouse_code)]
                    )
                    new_line_vals["warehouse"] = warehouse.id
                    if not warehouse:
                        raise UserError(
                            _("Warehouse with code %s not found")
                            % warehouse_code
                        )
                    new_line_vals["warehouse"] = warehouse.id
                else:
                    location_orig = self.env["stock.location"].search(
                        [("id", "=", row[2])]
                    )
                    if not location_orig:
                        raise UserError(
                            _("Location with id %s and name %s not found")
                            % row[2],
                            row[3],
                        )
                    new_line_vals["location"] = location_orig.id
            new_line = self.env["stock.in.out.line"].create(new_line_vals)
            new_line.onchange_warehouse()
            new_line.onchange_product()
        return {"type": "ir.actions.act_window_close"}
