# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class StockInventoryIssue(models.Model):

    # def _get_move_ids(self, location_id = False, product_id = False):
    #     domain = [('location_id', '=', location_id.id),
    #               ('location_dest_id', '=', location_id.id),
    #               ('product_id', '=', product_id.id)]
    #
    #     res = self.env['stock.move'].sudo().read_group(domain, ['id', 'product_id'], ['product_id'])
    #     self.move_ids = len(res)

    _name = "stock.inventory.issue"

    pending_qty = fields.Float("Cantidad pendiente")
    product_id = fields.Many2one("product.product")
    active = fields.Boolean("ACK", default=True)
    notes = fields.Char("Notas")
    read = fields.Boolean("Read from Mecalux")
    mecalux_qty = fields.Float("Qty read from Mecalux")
    odoo_qty = fields.Float("Qty read from Odoo")
    # move_ids = fields.Integer('Moves implied', compute="_get_move_ids")
    code = fields.Char("Product code")


class ProductProduct(models.Model):
    _inherit = "product.product"

    def compute_global_qty(self, location_id=False, force_company=False):
        company_no_stock_ids = (
            self.env["res.company"]
            .sudo()
            .search([("no_stock", "=", True)])
            .ids
        )

        domain = [
            ("product_id", "=", self.id),
            ("location_id", "=", location_id),
        ]
        if force_company:
            domain += [("company_id", "=", force_company)]
        else:
            domain += [("company_id", "not in", company_no_stock_ids)]
        quants_res = dict(
            (item["product_id"][0], item["qty"])
            for item in self.env["stock.quant"]
            .sudo()
            .read_group(domain, ["product_id", "qty"], ["product_id"])
        )
        global_qty = quants_res.get(self.id, 0.0)
        return global_qty


class StockInventoryLineSGA(models.Model):

    _inherit = "stock.inventory.line"

    from_sga = fields.Boolean("From mecalux", default=False)
    stock_mecalux = fields.Float(
        "Global stock (Mecalux)",
        digits=dp.get_precision("Product Unit of Measure"),
        readonly=True,
    )
    global_qty = fields.Float(
        "Global stock (Odoo)",
        compute="_compute_global_qty",
        digits=dp.get_precision("Product Unit of Measure"),
        readonly=True,
        store=True,
    )

    # @api.depends('location_id', 'product_id')
    @api.depends("location_id", "product_id")
    def _compute_global_qty(self):
        for line in self:
            line.global_qty = line.product_id.compute_global_qty(
                location_id=line.location_id.id
            )

    def _get_move_values(self, qty, location_id, location_dest_id):
        res = super(StockInventoryLineSGA, self)._get_move_values(
            qty, location_id, location_dest_id
        )
        res["company_id"] = self.company_id.id
        return res

    @api.model
    def search(self, args, offset=0, limit=0, order=None, count=False):
        if self._context.get("with_company", False):
            args += [("company_id", "=", self._context.get("with_company"))]

        return super(StockInventoryLineSGA, self).search(
            args, offset=offset, limit=limit, order=order, count=count
        )


class StockInventorySGA(models.Model):

    _inherit = "stock.inventory"

    def get_stock_query_from_mecalux(self):

        ids = self.env["sga.file"].process_sga_files(file_type="STO")
        view = self.env.ref("stock" ".view_inventory_tree")
        view_form = self.env.ref("stock" ".view_inventory_form")

        res = {
            "name": "Inventories",
            "view_type": "form",
            "view_mode": "tree,form",
            "domain": [("id", "in", ids)],
            "res_model": "stock.inventory",
            "type": "ir.actions.act_window",
            "view_id": False,
            "views": [(view.id, "tree"), (view_form.id, "form")],
        }
        return res

    def new_stock_query_to_mecalux(self):

        if not self.location_id.get_warehouse().sga_integrated:
            raise ValidationError(
                "Solo puedes consultar en stock en almacenes con Mecalux"
            )

        if self.state != "confirm":
            raise ValidationError(
                "Solo puedes consultar inventarios con estado: 'En Proceso'"
            )

        ids = [x.product_id.id for x in self.line_ids]
        new_sga_file = self.env["sga.file"].check_sga_file(
            "product.product", ids, code="PST"
        )
        return new_sga_file

    def import_inventory_STO(self, file_id):
        self.env["stock.inventory"].search(
            [
                ("name", "ilike", "MECALUX"),
                ("state", "in", ("draft", "confirm")),
            ]
        ).unlink()
        company_no_stock_ids = (
            self.env["res.company"]
            .sudo()
            .search([("no_stock", "=", True)])
            .ids
        )
        sga_file_obj = self.env["sga.file"].browse(file_id)

        sga_file_name = sga_file_obj.name
        log_name = u"{}.log".format(sga_file_name)
        sga_file = open(sga_file_obj.sga_file, "r")
        sga_file_lines = sga_file.readlines()

        sga_file.close()
        inventories = []
        warehouse_id = False

        line_number = 0

        cont = len(sga_file_lines)

        line_count = 0
        inserts = 0
        hora_inicio = datetime.now()
        str = "\nNumero de lineas a procesar: {}\nHora inicio: {}".format(
            cont, hora_inicio
        )
        sga_file_obj.write_log(str, log_name, False)

        str_to_write = ""
        force_write_log = False
        limit = self._context.get("sto_limit", False)
        for line in sga_file_lines:
            if limit and line_number > limit:
                break

            try:
                cont -= 1
                if len(line) < 420:
                    continue

                # POR RENDIMIENTO LO HAGO AL PRINCIPIO Y GENERICO
                # Warehouse code
                st = 0
                en = 10
                if not warehouse_id:
                    warehouse_code = line[st:en].strip()
                    warehouse_id = self.env["stock.warehouse"].search(
                        [("code", "=", warehouse_code)]
                    )
                    location_id = warehouse_id.lot_stock_id
                    # POR SEGURIDAD
                    if not warehouse_id.sga_integrated:
                        raise ValidationError("Solo almacenes con gestion SGA")

                # Product code
                st = en
                en += 50
                product_code = line[st:en].strip()
                # Empty fields
                st = en
                en += 50 + 50 + 14 + 12 + 50 + 14 + 14 + 20 + 50 + 12 + 3 + 50

                # quantity (int + dec >> float)
                st = 399
                st = en
                en += 7
                quantity_int = int(line[st:en])
                st = en
                en += 5
                quantity_dec = float("0." + line[st:en])
                mec_qty = quantity_int + quantity_dec

                product_id = self.env["product.product"].search(
                    [("default_code", "=", product_code)]
                )
                line_number += 1

                if (
                    force_write_log
                    or (line_number % 100 == 0)
                    and str_to_write != ""
                ):
                    sga_file_obj.write_log(str_to_write, log_name, False)
                    str_to_write = ""
                    force_write_log = False
                ## PROBLEMAS
                # NO ENCUENTRO EL PRODUCTO
                if not product_id:
                    print(
                        "Producto no encontrado: Linea {} Codigo {}".format(
                            line.replace("  ", "").strip(), product_code
                        )
                    )
                    issue_vals = {
                        "pending_qty": mec_qty,
                        "notes": "Articulo no encontrado en odoo %s"
                        % product_code,
                    }
                    self.env["stock.inventory.issue"].create(issue_vals)
                    str = "Error {} ({}) . Ref: {}. Qties: Mcx = {} NO ENCONTRADO EN ODOO".format(
                        "%05d" % cont,
                        "%05d" % line_count,
                        "{0: >16}".format(product_code),
                        "%010d" % mec_qty,
                    )
                    str_to_write = "{}\n{}".format(str_to_write, str)
                    force_write_log = True
                    # sga_file_obj.write_log(str_1, log_name, False)
                    continue

                # ENCUENTRO 2 PRODUCTOS CON EL MISMO CODIGO
                if len(product_id) > 1:
                    print(
                        "Codigo duplicado: Linea {} Codigo {}".format(
                            line.replace("  ", "").strip(), product_code
                        )
                    )
                    issue_vals = {
                        "notes": "Codigo duplicado: %s" % product_code,
                    }
                    self.env["stock.inventory.issue"].create(issue_vals)

                    str = "Error %s ({}) . Ref: {}. Qties: Mcx = {} DUPLICADO EN ODOO".format(
                        "%05d" % cont,
                        "%05d" % line_count,
                        "{0: >16}".format(product_code),
                        "%010d" % mec_qty,
                    )
                    str_to_write = "{}\n{}".format(str_to_write, str)
                    force_write_log = True
                    # sga_file_obj.write_log(str_1, log_name, False)
                    continue

                # eL PRODUCTO ES DE UNA COMPAÑIA QUE NO CUENTA STOCK
                product_company_id = product_id.company_id
                if product_company_id.id in company_no_stock_ids:
                    print(
                        "No stock product company: Linea {} Codigo {}".format(
                            line.replace("  ", "").strip(), product_code
                        )
                    )
                    str = "Error {} ({}) . Ref: {}. Qties: Mcx = {} COMPAÑIA SIN STOCK".format(
                        "%05d" % cont,
                        "%05d" % line_count,
                        "{0: >16}".format(product_code),
                        "%010d" % mec_qty,
                    )
                    str_to_write = "{}\n{}".format(str_to_write, str)
                    force_write_log = True
                    continue

                odoo_qty = product_id.compute_global_qty(
                    location_id=location_id.id
                )
                reg_qty_done = 0.00
                qty_to_reg = mec_qty - odoo_qty
                line_before = "STO linea  {} / {} [LEN: {}] >> OK >> Codigo: {} Cantidades: Odoo: {}, Mecalux: {} ".format(
                    line_number,
                    cont,
                    len(line),
                    product_code,
                    odoo_qty,
                    mec_qty,
                )
                print(line_before)
                original_qty = qty_to_reg
                if qty_to_reg != 0:
                    line_count += 1
                    str = "Linea {} ({}) . Ref: {}. QTies: Odoo = {} Mcx = {}".format(
                        "%05d" % cont,
                        "%05d" % line_count,
                        "{0: >16}".format(product_id.default_code),
                        "%010d" % odoo_qty,
                        "%010d" % mec_qty,
                    )
                    str_to_write = "{}\n{}".format(str_to_write, str)
                    inserts += 1
                    qty_to_reg, new_inventory, reg_qty = self.reg_stock(
                        product_id,
                        location_id,
                        product_company_id,
                        qty_to_reg,
                        mec_qty,
                        False,
                    )
                    reg_qty_done += reg_qty
                    if new_inventory:
                        inventories.append(new_inventory)

                    # PROBLEMA NO SE PUEDE REGULARIZAR
                    if qty_to_reg != 0.00:
                        print(
                            "No se puede regularizar: Linea {} Codigo {}".format(
                                line.replace("  ", "").strip(), product_code
                            )
                        )
                        issue_vals = {
                            "pending_qty": original_qty - reg_qty_done,
                            "product_id": product_id.id,
                            "notes": "No es posible regularizar",
                        }
                        self.env["stock.inventory.issue"].create(issue_vals)
                        str = "Error {} ({}) . Ref: {}. Qties: Mcx = {} No es posible regularizar la cantidad {}".format(
                            "%05d" % cont,
                            "%05d" % line_count,
                            "{0: >16}".format(product_code),
                            "%010d" % mec_qty,
                            "%010d" % qty_to_reg,
                        )
                        str_to_write = "{}\n{}".format(str_to_write, str)
                        force_write_log = True
                        continue

                ## TODO DE MOMENTO NO HACEMOS EL action_done, pendiente de confirmar que es automatico
                ##action_done = True if self.env['ir.config_parameter'].get_param('inventary_auto') == u'True' else False
                ##if action_done:
                ##    for stock_inv in inventories:
                ##        stock_inv.sudo().action_done()

            except:
                sga_file_obj.write_log(
                    "\n-----------------\n     ERROR:\n     {}\n".format(line),
                    log_name,
                    False,
                )
                sga_file_obj.write_log(
                    "\n    ULTIMA: {}\n-----------------".format(str_to_write),
                    log_name,
                    False,
                )
                force_write_log = True

        if str_to_write:
            sga_file_obj.write_log(str_to_write, log_name, False)

        if inventories:
            inventories = list(set(inventories))
            sga_file_obj.write_log(
                "Inventarios creados con {}".format(inventories),
                log_name,
                False,
            )

        end_str = "\nNumero de lineas a crear: {}\nHora fin: {} Tiempo empleado: {}".format(
            inserts, datetime.now(), datetime.now() - hora_inicio
        )
        sga_file_obj.write_log(end_str, log_name, False)

        return inventories

    def new_inv_line(self, product_id, qty, inventory_id, mecalux_stock=0.00):

        # Si hay alguno pendiente lo borro
        domain = [
            ("product_id", "=", product_id.id),
            ("location_id", "=", inventory_id.location_id.id),
            ("company_id", "=", inventory_id.company_id.id),
            ("state", "in", ("draft", "confirm")),
        ]
        inventory_line = self.env["stock.inventory.line"].search(domain)

        if inventory_line:
            inventory_line.unlink()
        new_line_vals = {
            "product_id": product_id.id,
            "product_qty": qty,
            "stock_mecalux": mecalux_stock,
            "inventory_id": inventory_id.id,
            "company_id": inventory_id.company_id.id,
            "location_id": inventory_id.location_id.id,
            "from_sga": True,
        }
        new_inventory_line = (
            self.env["stock.inventory.line"].sudo().create(new_line_vals)
        )
        return new_inventory_line

    def get_inventory_for(self, product_id, location_id, company_id):

        # miro si hay un inventario abierto para esta compañia y si no lo creo
        domain = [
            ("location_id", "=", location_id.id),
            ("company_id", "=", company_id.id),
            ("filter", "=", "partial"),
            ("state", "=", "confirm"),
        ]
        inventory = self.env["stock.inventory"].search(domain)

        if not inventory:
            stock_inv_vals = {
                "name": u"%s (%s)" % ("MECALUX / ", company_id.ref),
                "location_id": location_id.id,
                "filter": "partial",
                "company_id": company_id.id,
            }
            inventory = (
                self.env["stock.inventory"].sudo().create(stock_inv_vals)
            )
        inventory = inventory[0]
        inventory.action_start()
        return inventory

    def reg_stock(
        self,
        product_id,
        location_id,
        company_id,
        qty_to_reg,
        mec_qty,
        force_company=False,
    ):

        if not product_id or not location_id or not company_id:
            return 0.00, False

        ctx = self._context.copy()

        # Menos en Odoo: Si hay en palla negativos se pone a cero
        if qty_to_reg > 0:
            company_id = product_id.company_id
            inventory_id = self.get_inventory_for(
                product_id, location_id, company_id
            )
            ctx.update({"with_company": company_id.id})
            new_inv_line = self.with_context(ctx).new_inv_line(
                product_id, 0.0, inventory_id, mec_qty
            )
            new_inv_line.product_qty = (
                new_inv_line.theoretical_qty + qty_to_reg
            )
            return 0.00, inventory_id.id, qty_to_reg

        # Hay mas en Odoo que mecalux
        elif qty_to_reg < 0:
            inventory_id = self.get_inventory_for(
                product_id, location_id, company_id
            )
            ctx.update({"with_company": company_id.id})
            new_inv_line = self.with_context(ctx).new_inv_line(
                product_id, 0.0, inventory_id, mec_qty
            )
            new_inv_line.product_qty = (
                new_inv_line.theoretical_qty + qty_to_reg
            )
            return 0.00, inventory_id.id, qty_to_reg

    def reg_stock1(
        self,
        product_id,
        location_id,
        company_id,
        qty_to_reg,
        mec_qty,
        force_company=False,
    ):

        if not product_id or not location_id or not company_id:
            return 0.00, False

        ctx = self._context.copy()

        # Menos en Odoo: Si hay en palla negativos se pone a cero
        if qty_to_reg > 0:
            force_company_qty = 0.00
            if force_company:
                # Busco stock en Pallatium, si hay fuerzo la compañia
                force_company = self.env["res.company"].search(
                    [("ref", "=", "PALLAT")]
                )
                force_company_qty = product_id.compute_global_qty(
                    location_id=location_id.id, force_company=force_company.id
                )
                if force_company_qty < 0.00:
                    # Hay negativos
                    company_id = force_company
                    max_qty_to_reg = min(qty_to_reg, -force_company_qty)
                    inventory_id = self.get_inventory_for(
                        product_id, location_id, company_id
                    )
                    ctx.update({"with_company": company_id.id})
                    new_inv_line = self.with_context(ctx).new_inv_line(
                        product_id, 0.0, inventory_id, mec_qty
                    )
                    new_inv_line.product_qty = (
                        new_inv_line.theoretical_qty + max_qty_to_reg
                    )
                    qty_to_reg -= max_qty_to_reg
                    return qty_to_reg, inventory_id.id, max_qty_to_reg
                else:
                    return qty_to_reg, False, 0.00
            else:
                # No hay negativos en pallatium
                company_id = product_id.company_id
                inventory_id = self.get_inventory_for(
                    product_id, location_id, company_id
                )
                ctx.update({"with_company": company_id.id})
                new_inv_line = self.with_context(ctx).new_inv_line(
                    product_id, 0.0, inventory_id, mec_qty
                )
                new_inv_line.product_qty = (
                    new_inv_line.theoretical_qty + qty_to_reg
                )
                return 0.00, inventory_id.id, qty_to_reg

        # Hay mas en Odoo que mecalux
        elif qty_to_reg < 0:
            inventory_id = self.get_inventory_for(
                product_id, location_id, company_id
            )
            ctx.update({"with_company": company_id.id})
            new_inv_line = self.with_context(ctx).new_inv_line(
                product_id, 0.0, inventory_id, mec_qty
            )
            new_inv_line.product_qty = (
                new_inv_line.theoretical_qty + qty_to_reg
            )
            return 0.00, inventory_id.id, qty_to_reg

    def global_stock_mecalux(self):
        if self.location_id.barcode != "PLS":
            raise ValidationError("Solo para almacen de Palas")

        if self.line_ids:
            self.env["sga.file"].create_global_PST()
        else:
            raise ValidationError(
                "Si quieres selccionar productos, debes hacerlo desde la vista tree de productos"
            )

    def action_done(self):
        ## sobre escribo la función para cambiar el signo en caso de pallatium
        if self.company_id.vat:
            return super(StockInventorySGA, self).action_done()

        negative = next(
            (
                line
                for line in self.mapped("line_ids")
                if line.product_qty < 0
                and line.product_qty < line.theoretical_qty
            ),
            False,
        )
        if negative:
            raise UserError(
                _(
                    "You cannot set a negative product quantity greater than teorical quatity in an inventory line:\n\t%s - qty: %s"
                )
                % (negative.product_id.name, negative.product_qty)
            )
        self.action_check()
        self.write({"state": "done"})
        self.post_inventory()
        return True
