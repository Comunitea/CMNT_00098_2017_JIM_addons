# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re

class ModelSgafile2(models.Model):

    _inherit = 'sgavar.file'



    def import_ctes(self):


        ###########################
        #importamos clientes
        name = 'Clientes'
        code = 'ACC'
        version = '04'
        model = 'res.partner'
        fields = [('operation', 1, 'A', 'F'), ('account_code', 12, 'A', '', 'ref'), ('name', 80, 'A', ''),
                  ('outbound_priority', 10, 'N', '50'), ('addr_name', 255, 'A', '0'), ('addr_line1', 30, 'A', ''),
                  ('addr_line2', 30, 'A', ''), ('city', 25, 'A', ''), ('state', 2, 'A', ''), ('country', 15, 'A', ''),
                  ('zip', 10, 'A', ''), ('contact_name', 30, 'A', ''), ('contact_tel', 12, 'A', ''),
                  ('contact_ext', 12, 'A', ''), ('contact_fax', 12, 'A', ''), ('comment_', 30, 'A', ''),
                  ('containertype_code', 10, 'A', ''), ('desc_conttype_code', 60, 'A', ''),
                  ('carrier_code', 20, 'A', ''), ('description', 255, 'A', ''), ('terms', 2000, 'A', ''),
                  ('company_code', 12, 'A', ''), ('rec_hours_from_mon', 14, 'D', ''), ('rec_hours_to_mon', 14, 'D', ''),
                  ('rec_hours_from_tue', 14, 'D', ''), ('rec_hours_to_tue', 14, 'D', ''),
                  ('rec_hours_from_wed', 14, 'D', ''), ('rec_hours_to_wed', 14, 'D', ''),
                  ('rec_hours_from_thu', 14, 'D', ''), ('rec_hours_to_thu', 14, 'D', ''),
                  ('rec_hours_from_fri', 14, 'D', ''), ('rec_hours_to_fri', 14, 'D', ''),
                  ('rec_hours_from_sat', 14, 'D', ''), ('rec_hours_to_sat', 14, 'D', ''),
                  ('rec_hours_from_sun', 14, 'D', ''), ('rec_hours_to_sun', 14, 'D', ''),
                  ('formattype_code', 10, 'A', ''), ('allow_split', 1, 'B', ''), ('active_fusion', 1, 'B', ''),
                  ('attribute', 20, 'V', ''), ('line_number', 10, 'N', '0')]

        self.import_ctes2(name, code, version, model, fields)



        name = "Tipos de productos"
        code = "TPR"
        version= "01"
        model = 'product.category'
        fields = [('operation', 1, 'A', 'F'), ('producttype_code', 12, 'A', 'sga_producttype_code'), ('description', 80, 'A', '', 'name'),
                  ('parent_producttype_code', 12, 'A', 'parent_id','sga_producttype_code'), ('attribute', 20, 'V', '')]
        self.import_ctes2(name, code, version, model, fields)

        name = "Transportistas"
        code = "CAR"
        version = "01"
        model = "delivery.charge"
        fields = [('operation', 1, 'A', 'F'), ('carrier_code', 20, 'A', ''), ('carrier_name', 40, 'A', '', 'name'),
                  ('description', 250, 'A', ''), ('contact', 60, 'A', ''), ('attribute', 20, 'V', ''), ]
        self.import_ctes2(name, code, version, model, fields)


        name = "Productos"
        code = "PRO"
        version = "05"
        model = "product.template"
        fields = [('operation', 1, 'A', 'F'), ('product_code', 50, 'A', ''), ('new_product_code', 50, 'A', ''),
                  ('ean_code', 50, 'A', ''), ('producttype_code', 12, 'A', ''), ('change_material_abc', 1, 'B', '1'),
                  ('material_abc_code', 2, 'A', 'C'), ('avg_cost_packtype', 10, 'A', ''),
                  ('desc_avg_cost_packtype', 30, 'A', ''), ('supplier_code', 20, 'A', ''),
                  ('date_control', 1, 'B', '0'), ('serial_no_control', 1, 'B', '0'), ('lot_control', 1, 'B', '0'),
                  ('mixed_lots', 1, 'B', '0'), ('catch_weight', 1, 'B', '0'), ('random_weight', 1, 'B', '0'),
                  ('movement_packtype', 50, 'A', ''), ('desc_movement_pack_type', 30, 'A', ''),
                  ('order_packsize', 10, 'A', ''), ('desc_ order_packsize', 30, 'A', ''),
                  ('shipping_packtype', 10, 'A', ''), ('desc_shipping_packtype', 30, 'A', ''),
                  ('prod_desc', 255, 'A', ''), ('prod_altdesc', 255, 'A', ''), ('prod_shortdesc', 50, 'A', ''),
                  ('shelf_life', 12.5, 'N', ''), ('avg_cost', 19.4, 'N', ''), ('receive_life', 12.5, 'N', ''),
                  ('container_stack', 10, 'N', ''), ('pick_warn_message', 30, 'A', ''), ('verify_metrics', 1, 'B', ''),
                  ('uom_base_code', 10, 'A', ''), ('desc_uom_base_code', 30, 'A', ''), ('allow_split', 1, 'B', ''),
                  ('allow_commingle', 1, 'B', ''), ('hazard_code', 12, 'A', ''), ('overcase_percent', 5.2, 'N', ''),
                  ('product_subtype_code', 12, 'A', ''), ('quality_control', 1, 'B', '0'),
                  ('owner_control', 1, 'B', '0'), ('owner_code', 12, 'A', ''), ('containertype_code', 10, 'A', ''),
                  ('package', 1, 'B', ''), ('outbound_logic', 2, 'A', ''), ('lot_formula', 50, 'A', ''),
                  ('coded', 1, 'B', '0'), ('req_lot_rec', 1, 'B', '0'), ('req_lot_exp', 1, 'B', '0'),
                  ('req_manipulation', 1, 'B', '0'), ('manipulation_desc', 100, 'A', ''),
                  ('rec_more_percent', 5.2, 'N', ''), ('under_weight_percent', 5.2, 'N', ''),
                  ('over_weight_percent', 5.2, 'N', ''), ('temp_min', 5.2, 'N', ''), ('temp_max', 5.2, 'N', ''),
                  ('sust_max_percent', 5.2, 'N', ''), ('pp_format', 2, 'A', ''), ('nested_uom_code', 10, 'A', ''),
                  ('inbound_subware_code', 10, 'A', ''), ('max_height', 12.5, 'N', ''), ('min_height', 12.5, 'N', ''),
                  ('merge_days', 12.5, 'N', ''), ('max_stock', 12.5, 'N', ''), ('min_stock', 12.5, 'N', ''),
                  ('lot_control_noexact', 1, 'B', ''), ('supplier_control', 1, 'B', ''), ('attribute', 20, 'V', ''),
                  ('lines_number', 10, 'N', 'product_uom_ids')]
        self.import_ctes2(name, code, version, model, fields)

        name = "Presentaciones / UOM"
        code = "PUI"
        version = ""
        model = "product.uom"
        fields = [('start_string', 1, 'A', '‘/’'), ('operation', 1, 'A', ''), ('uom_code', 10, 'A', ''),
                  ('uom_desc', 30, 'A', ''), ('quantity', 12.5, 'N', ''), ('pack_weight', 12.5, 'N', ''),
                  ('lenght', 12.5, 'N', ''), ('width', 12.5, 'N', ''), ('height', 12.5, 'N', ''),
                  ('prep_time', 12.5, 'N', ''), ('containertype_code', 10, 'A', ''),
                  ('desc_containertype_code', 60, 'A', ''), ('quantity_conttype', 12.5, 'N', ''), ('tie', 5, 'N', ''),
                  ('hight', 5, 'N', ''), ('pick_neg_percent', 3, 'N', ''), ('pick_comp_percent', 3, 'N', ''),
                  ('complete_percent', 3, 'N', ''), ('preferable', 1, 'B', ''), ('required', 1, 'B', ''),
                  ('lock_from', 14, 'D', ''), ('lock_to', 14, 'D', ''), ('min_quantity', 12.5, 'N', ''),
                  ('container_height', 12.5, 'N', '')]
        self.import_ctes2(name, code, version, model, fields)


        name = "Peticion de Stock"
        code = "PST"
        version = "03"
        model = "product.template"
        fields = [('warehouse_code', 10, 'A', 'PS'), ('product_code', 50, 'A', '', 'ref'), ('lot_code', 50, 'A', ''),
                  ('serial_no', 50, 'A', ''), ('exp_date', 14, 'D', ''), ('owner_code', 12, 'A', ''),
                  ('status_code', 3, 'A', ''), ('quality', 50, 'A', ''), ('best_before_date', 14, 'D', ''),
                  ('shelf_life', 12.5, 'N', ''), ('tipo_de_peticion', 1, 'A', 'T')]
        self.import_ctes2(name, code, version, model, fields)

        model='stock.picking'
        name="Albaranes de Entrada"
        fields = [('operation', 1, 'A', 'F'), ('rec_order_code', 30, 'A', ''), ('warehouse_code', 10, 'A', ''), (
        'supplier_code', 20, 'A', '', 'ref'), ('carrier_code', 20, 'A', ''), ('document', 50, 'A', ''), (
               'transport_type', 50, 'A', ''), ('main_transport', 50, 'A', ''), ('aux_transport', 50, 'A', ''), (
               'source', 50, 'A', ''), ('description', 100, 'A', ''), ('expected_date', 14, 'D', ''), (
               'containers', 12.5, 'N', ''), ('order_type', 30, 'A', ''), ('account_code', 12, 'A', ''), (
               'company', 50, 'A', ''), ('days_from_rec', 12.5, 'N', ''), ('door_code', 12, 'A', ''), (
               'attribute', 20, 'V', ''), ('numero_lineas', 10, 'N', 'move.lines')]
        code = "PRE"
        version ="04"
        self.import_ctes2(name, code, version, model, fields)

        name="Lineas Albaranes de Entrada"
        model= 'stock.move'
        fields=[('caracter_inicio', 1, 'A', '/'), ('product_code', 50, 'A', ''), ('quantity', 12.5, 'N', ''), (
                'uom_code', 10, 'A', ''), ('lote', 50, 'A', ''), ('exp_date', 14, 'D', ''), ('serial', 50, 'A', ''), (
               'owner_code', 12, 'A', ''), ('container_no', 50, 'A', ''), ('stock_status_code', 3, 'A', ''), (
               'req_manipulation', 1, 'B', '0'), ('manipulation_desc', 100, 'A', ''), (
               'purchase_price', 12.5, 'N', ''), ('receive_life', 12.5, 'N', ''), ('line_number', 10, 'N', '')]
        code=""
        version=""
        self.import_ctes2(name, code, version, model, fields)

        name="Pedidos de ventas"
        fields=[('operation', 1, 'A', 'F'), ('sorder_code', 50, 'A', ''), ('warehouse_code', 10, 'A', 'PLS'), (
                'description', 100, 'A', ''), ('comment_', 255, 'A', ''), ('type_code', 30, 'A', ''), (
               'type_description', 100, 'A', ''), ('priority', 10, 'N', ''), ('account_code', 12, 'A', ''), (
               'staging_loc_code', 12, 'A', ''), ('door_code', 12, 'A', ''), ('route_code', 50, 'D', ''), (
               'stop_number', 10, 'N', ''), ('carrier_code', 20, 'A', ''), ('containertype_code', 10, 'A', ''), (
               'document', 50, 'A', ''), ('transport_type', 50, 'A', ''), ('source', 50, 'A', ''), (
               'delivery_inst', 255, 'A', ''), ('allocate_date', 14, 'D', ''), ('process_date', 14, 'D', ''), (
               'shipping_date', 14, 'D', ''), ('planned_load_date', 14, 'D', ''), ('containers', 12.5, 'N', ''), (
               'verify_stock', 1, 'B', '0'), ('follow_sequence', 1, 'B', ''), ('release_date', 14, 'D', ''), (
               'supplier_code', 20, 'A', '', 'ref'), ('attribute', 20, 'V', ''), ('numero_lineas', 10, 'N', '')]
        code="SOR"
        version="07"
        self.import_ctes2(name, code, version, model, fields)

        name="Lineas de Pedidos de ventas"
        fields=[('caracter_inicio', 1, 'A', '/'), ('line_number', 10, 'N', ''), ('product_code', 50, 'A', ''), (
        'lot_code', 50, 'A', ''), ('quantity', 12.5, 'N', ''), ('ean_code', 50, 'A', ''), ('serial_no', 50, 'A', ''), (
               'shelf_days', 14, 'D', ''), ('uom_code', 10, 'A', ''), ('required_to_ship', 1, 'B', ''), (
               'comment', 255, 'A', ''), ('is_critical', 1, 'B', ''), ('custsp_line_no', 50, 'A', ''), (
               'expected_date', 14, 'D', ''), ('customer_code', 50, 'A', ''), ('require_status_code', 3, 'A', ''), (
               'reject_status_code', 3, 'A', ''), ('owner_code', 12, 'A', ''), ('pre_req_status_code', 3, 'A', ''), (
               'container_no', 50, 'A', ''), ('quantity_to_reserve', 12.5, 'N', ''), ('serie_control', 1, 'B', ''), (
               'sale_price', 12.5, 'N', ''), ('labels_no', 3, 'N', ''), ('containertype_code', 10, 'A', '0'), (
               'substitute_prod_code', 50, 'A', ''), ('preferable_uom_code', 10, 'A', ''), (
               'min_shelf_life', 12.5, 'N', ''), ('round_control', 1, 'B', ''), ('mixed_logistic', 1, 'B', ''), (
               'quality', 50, 'A', ''), ('best_before_date', 14, 'D', ''), ('location_label', 20, 'A', ''), (
               'catch_weight', 1, 'B', '0'), ('sustitute_qtty', 12.5, 'N', '0'), ('disable_alt_product', 1, 'B', '1'), (
               'alt_uom_code', 10, 'A', ''), ('from_factor', 5, 'N', ''), ('to_factor', 5, 'N', ''), (
               'attribute', 20, 'V', '')]
        code=""
        version=""

        self.import_ctes2(name, code, version, model, fields)


    def import_ctes2(self, name, code, version, model, fields):
        print "\n\n\nIMPORTANDO %s"%name
        val = {
            'name': name,
            'code': code,
            'version': version,
            'odoo_model': self.env['ir.model'].search([('name','=', model)]),
            'cte_name': ""
        }
        new_sgavar_file = self.create(val)
        ids = []


        for var in fields:
            #import ipdb; ipdb.set_trace()

            val = {
                'name':var[0],
                'length': var[1],
                'mecalux_type': var[2],
                'fillchar': " " if var[2] in ['A','B','V'] else '0',
                'default':var[3],
                'sga_file_id': new_sgavar_file.id
            }

            new_var = self.env['sgavar.file.var'].create(val)
            new_sgavar_file.write({'sga_file_var_ids': [(4, [new_var.id])]})
