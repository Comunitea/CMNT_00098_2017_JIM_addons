# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime,timedelta
from odoo.osv import expression


class IrCron(models.Model):
    _inherit = 'ir.cron'

    last_call = fields.Datetime('Last call')


class ConfigPathFiles(models.TransientModel):
    _inherit = 'res.config.settings'

    last_call_export_xmlstock = fields.Char('Last call export xml_stock')

    @api.model
    def get_default_last_call_export_xmlstock(self, fields):
        res = {}
        icp = self.env['ir.config_parameter']
        res['last_call_export_xmlstock'] = icp.get_param(
            'last_call_export_xmlstock')
        return res

    @api.multi
    def set_last_call_export_xmlstock(self):
        icp = self.env['ir.config_parameter']
        icp.set_param('last_call_export_xmlstock',
                      self.last_call_export_xmlstock)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    def compute_up_insert_product_ids(self, product_ids=False):

        up_bom_line_domain = [('bom_id.id', 'not in', self.ids), ('product_id', 'in', product_ids.ids)]
        up_bom = self.env['mrp.bom.line'].search(up_bom_line_domain).mapped('bom_id')
        if up_bom:
            new_product_ids = up_bom.compute_self_product_ids()
            product_ids |= new_product_ids
            product_ids |= up_bom.compute_up_insert_product_ids(new_product_ids)


            # up_bom_product_ids = up_bom.compute_self_product_ids() - product_ids
            # product_ids |= up_bom_product_ids
            # product_ids |= up_bom.compute_up_insert_product_ids(up_bom_product_ids)
        return product_ids

    @api.multi
    def compute_down_insert_product_ids(self):
        product_ids = self.mapped('bom_line_ids').mapped('product_id')
        down_bom_domain = [('id', 'not in', self.ids), '|', ('product_tmpl_id', 'in', product_ids.mapped('product_tmpl_id').ids), ('product_id', 'in', product_ids.ids)]
        down_bom_ids = self.env['mrp.bom'].search(down_bom_domain)
        if down_bom_ids:
            product_ids |= down_bom_ids.compute_down_insert_product_ids()
            # product_ids |= down_bom_ids.compute_self_product_ids()
            # product_ids |= down_bom_ids.compute_down_insert_product_ids()
        return product_ids

    @api.multi
    def compute_self_product_ids(self):
        return self.mapped('product_tmpl_id').mapped('product_variant_ids') | self.mapped('product_id')


    @api.multi
    def compute_insert_product_ids(self):

        product_ids = self.compute_self_product_ids()
        product_ids_up = self.compute_up_insert_product_ids(product_ids)
        product_ids_down = self.compute_down_insert_product_ids()
        product_ids |= product_ids_up
        product_ids |= product_ids_down
        return product_ids

    @api.multi
    def insert_product_ids(self):
        product_ids = self.compute_insert_product_ids()
        return product_ids; #self.env['exportxml.object'].insert_product_ids(product_ids, self._name)

    @api.model
    def create(self, vals):
        bom = super(MrpBom, self).create(vals)
        bom.insert_product_ids()
        return bom

    @api.multi
    def write(self, vals):
        bom = super(MrpBom, self).write(vals)
        self.insert_product_ids()
        return bom

    @api.multi
    def unlink(self):
        self.insert_product_ids()
        return super(MrpBom, self).unlink()

    @api.multi
    def export_related_bom_ids(self, product_ids):
        line_domain = [('product_id', 'in', product_ids.ids)]
        bom_ids = self.env['mrp.bom.line'].search(line_domain).mapped('bom_id')
        bom_domain = ['|', ('product_tmpl_id', 'in', product_ids.mapped('product_tmpl_id').ids), ('product_id', 'in', product_ids.ids)]
        bom_ids |= self.env['mrp.bom'].search(bom_domain)
        return bom_ids.compute_insert_product_ids()

class MrpBomLine(models.Model):

    _inherit = 'mrp.bom.line'

    @api.multi
    def insert_product_ids(self):
        return self.mapped('bom_id').insert_product_ids()

    @api.model
    def create(self, vals):
        bom_line = super(MrpBomLine, self).create(vals)
        bom_line.insert_product_ids()
        return bom_line

    @api.multi
    def write(self, vals):
        bom_line = super(MrpBomLine, self).write(vals)
        self.insert_product_ids()
        return bom_line

    @api.multi
    def unlink(self):
        self.insert_product_ids()
        return super(MrpBomLine, self).unlink()

class StockLocation(models.Model):

    _inherit = 'stock.location'

    @api.multi
    def write(self, vals):
        res = super(StockLocation, self).write(vals)
        fields_to_check = ['location_id', 'usage', 'scrap_location', 'deposit']
        if any(field in vals.keys() for field in fields_to_check):
            location_ids = self
            #location_ids |= self.mapped('child_ids')
            product_ids = []
            domain = [('location_id', 'child_of', location_ids.ids)]
            res = self.env['stock.quant'].read_group(domain, ['qty', 'product_id'], ['product_id'])
            for res_id in res:
                if res_id['qty'] > 0:
                    product_ids.append(res_id['product_id'][0])
            # if product_ids:
            #     self.env['exportxml.object'].insert_product_ids(self.browse(product_ids), self._name)

        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def unlink(self):
        self.insert_product_ids()
        return super(SaleOrder, self).unlink()

    @api.multi
    def insert_product_ids(self):
        return self.mapped('order_line').insert_product_ids()



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def unlink(self):
        self.insert_product_ids()
        return super(PurchaseOrder, self).unlink()

    @api.multi
    def insert_product_ids(self):
        return self.mapped('order_line').insert_product_ids()

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def unlink(self):
        self.mapped('move_lines').unlink()
        return super(StockPicking, self).unlink()

class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def unlink(self):
        if self:
            ## No se poq a veces entra con self vacío
            location_domain = self.get_locations_domain()
            ids_domain = [('id', 'in', tuple(self.ids))] if len(self) > 1 else [('id','=', self.id)]
            domain = expression.AND([ids_domain, location_domain])
            to_unlink = self.search(domain)
            if to_unlink:
                to_unlink.do_unreserve()
                to_unlink.insert_product_ids()
        return super(StockMove, self).unlink()

    def get_locations_domain(self):
        lcoation_domain = ['|', '|', '|', ('location_dest_id.deposit', '=', True), ('location_dest_id.deposit', '=', True), ('location_id.scrap_location', '=', True), ('location_dest_id.scrap_location', '=', True)]
        in_domain = expression.normalize_domain([('location_id.usage', '!=', 'internal'), ('location_dest_id.usage', '=', 'internal')])
        out_domain  = expression.normalize_domain([('location_id.usage', '=', 'internal'), ('location_dest_id.usage', '!=', 'internal')])
        domain = expression.OR([lcoation_domain, in_domain, out_domain])
        return expression.normalize_domain(domain)


    def get_stock_export_products(self, from_time, to_time = False, table=False, sql=False):
        product_ids = self.env['product.product']
        time_domain = self.env['exportxml.object'].get_time_domain(from_time, to_time, False)
        internal = self.get_locations_domain()
        domain = expression.normalize_domain(expression.AND([time_domain, internal]))
        sol = self.search(domain)
        if table:
            product_ids = sol.insert_product_ids()
        else:
            product_ids = sol.mapped('product_id')

        return product_ids

    @api.multi
    def insert_product_ids(self, product_ids= False):
        if not product_ids:
            product_ids = self.mapped('product_id')
        # if product_ids:
        #     self.env['exportxml.object'].insert_product_ids(product_ids, self._name)
        return product_ids

class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'


    @api.multi
    def insert_product_ids(self):
        ##busco las líneas de venta que no tenga movimientos asignados. Si tienen movimientos ya no influye el cambio
        sol_domain = [('route_id', 'in', self.ids), ('order_id.state', 'not in', ('sale', 'done', 'cancel'))]
        return self.env['sale.order.line'].search(sol_domain).insert_product_ids()

    @api.multi
    def write(self, vals):
        fields_to_check = ['no_stock', 'virtual_type']
        if any(field in vals.keys() for field in fields_to_check):
            self.insert_product_ids()
        return super(StockLocationRoute, self).write(vals)

class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    @api.multi
    def insert_product_ids(self):
        product_ids = self.mapped('product_id')
        # if product_ids:
        #     self.env['exportxml.object'].insert_product_ids(product_ids, self._name)
        return product_ids

    @api.multi
    def unlink(self):
        to_unlink = self.filtered(lambda x: x.state not in ('cancel', 'draft'))
        if to_unlink:
            self.insert_product_ids()
        return super(PurchaseOrderLine, self).unlink()

    def get_stock_export_products(self, from_time, to_time=False, table=False):
        product_ids = self.env['product.product']
        return product_ids

class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def insert_product_ids(self):
        product_ids = self.mapped('product_id')
        # if product_ids:
        #     self.env['exportxml.object'].insert_product_ids(product_ids, self._name)
        return product_ids

    @api.multi
    def unlink(self):
        to_unlink = self.filtered(lambda x: not x.route_id.no_stock or x.state not in ('cancel', 'draft'))
        if to_unlink:
            self.insert_product_ids()
        return super(SaleOrderLine, self).unlink()



    def get_stock_export_products(self, from_time, to_time = False, table=False):

        time_domain = self.env['exportxml.object'].get_time_domain(from_time, to_time, 'order_id')
        state_domain = [('state', 'in', ('cancel', 'draft', 'lqdr', 'pending'))]
        product_domain = [('product_id.type', '=', 'product')]
        domain = expression.AND([product_domain, state_domain, time_domain])
        sol = self.search(domain)
        if table:
            product_ids = sol.insert_product_ids()
        else:
            product_ids = sol.mapped('product_id')
        return product_ids

class DeletedObject(models.Model):

    _name = 'exportxml.object'

    ## Necesito asociar aquí todos los productos de : Linea de venta, moves, mrp.bom.lines borradas
    product_id = fields.Many2one('product.product')
    model = fields.Char('model')
    _sql_constraints = [
        ('product_id_uniq', 'unique(product_id)', _("A product_id can only be assigned to one product !")),
    ]

    def get_time_domain(self, from_time, to_time, field_parent_id = False):
        def get_domain(field):
            domain = [(field,'>=', from_time)]
            if to_time:
                domain += [(field,'<=', to_time)]
            return expression.normalize_domain(domain)

        domain = get_domain('create_date')
        domain = expression.OR([domain, get_domain('write_date')])
        if field_parent_id:
            domain = expression.OR([domain, get_domain('{}.create_date'.format(field_parent_id))])
            domain = expression.OR([domain, get_domain('{}.write_date'.format(field_parent_id))])
        return expression.normalize_domain(domain)

    def compute_product_stock(self):
        fields.Datetime.now()

    @api.model
    def compute_product_ids_xmlrpc(self, values):
        all = values.get('all', False)
        table = values.get('table', True)
        days = values.get('days', 1)
        from_time = values.get('from_time', False)
        to_time = values.get('to_time', False)
        field_id = values.get('field_id', 'id')
        stock_field = values.get('stock_field', 'web_global_stock')
        inc = values.get('inc', 80)
        return self.compute_product_ids(all, table, from_time, to_time, field_id, stock_field, days, inc)

    def test_compute_product_ids_bucle_check_performance(self):
        mid_time = time.time()
        for inc in [80,500,2500,5000,80,500,2500,5000]:
            res = self.compute_product_ids(inc=inc)
            print ("---- {} resultados en {}".format(len(res),time.time() - mid_time)); mid_time = time.time()

    def compute_product_ids_all(self):
        values = {'all': True}
        return self.compute_product_ids_xmlrpc(values)

    def compute_product_ids(self, all=False, table=False, from_time=False, to_time=False, field_id='id', stock_field='web_global_stock', days=0, inc=80, limit=False):
        time_now = fields.datetime.now()
        time_now_str = fields.Datetime.to_string(time_now)
        sql_ir_config = "select value from  ir_config_parameter where key = 'last_call_export_xmlstock'"
        self._cr.execute(sql_ir_config)
        res_id = self._cr.fetchall()
        if res_id:
            last_call = res_id[0][0]
        if not last_call:
            last_call = time_now_str
        start_time = time.time()
        if not from_time:
            #from_time = fields.Datetime.from_string(last_call)
            from_time = last_call
        if not to_time and days > 0:
            ##No debería entrar aquí nuca
            from_time_str = fields.Datetime.from_string(from_time)
            to_time = fields.Datetime.to_string(from_time_str + timedelta(days=days))
        print ("Comenzando la exportación desde {} hasta {}".format(from_time, to_time))

        ##stock.location.route, stock.location,mrp.bom, mrp.bom.line lo hacen en write/create

        print ("#######################\nFiltrando productos ....")
        if table:
            print ("-- Usando tabla intermedia")
        if not all:
            print ("-- Solo compras, ventas y movimientos de stock")
        mid_time = time.time()

        p_ids = self.env['sale.order.line'].sudo().get_stock_export_products(from_time, to_time, table)
        print ("---- {} productos de ventas en {}".format(len(p_ids),time.time() - mid_time)); mid_time = time.time()
        purchase_ids = self.env['purchase.order.line'].sudo().get_stock_export_products(from_time, to_time,  table)
        p_ids |= purchase_ids
        print ("---- {} productos de compras en {}".format(len(purchase_ids),time.time() - mid_time)); mid_time = time.time()
        move_ids = self.env['stock.move'].sudo().get_stock_export_products(from_time, to_time, table)
        print ("---- {} productos de movimientos en {}".format(len(move_ids),time.time() - mid_time)); mid_time = time.time()
        p_ids |= move_ids
        product_table_ids = self.env['product.product']
        if all:
            domain = []
        else:
            domain = [('model', 'in', ('product.product', 'sale.order.line', 'stock.move', 'purchase.order.line'))]
        if table or all:
            table_ids = self.search(domain)
            product_table_ids = table_ids.mapped('product_id')
            model_ids = table_ids.mapped('model')
            print ("--Tabla de productos")
            print ("---- {} modelos en la tabla".format(len(model_ids)))
            print ("---- {} productos en la tabla".format(len(product_table_ids)))
        if table:
            product_ids = product_table_ids
        else:
            product_ids = product_table_ids | p_ids


        if product_ids:
            mid_time = time.time()
            product_bom_ids = self.env['exportxml.object'].insert_product_ids(product_ids)
            product_ids |= product_bom_ids
            print ("---- {} productos de listas de materiales en {}".format(len(product_bom_ids),time.time() - mid_time)); mid_time = time.time()
        print ("-- Total: {} productos a evaluar en {}".format(len(product_ids), time.time() - mid_time)); mid_time = time.time()
        total = len(product_ids)
        res= []
        cont=0
        while cont < total:
            if limit and cont>limit:
                print ("limite {} alacanczo de prodictos".format(limit))
                break
            cont += inc
            print ("-- Evaluando de {} a {}".format(cont-inc, cont)); mid_time = time.time()
            res += [{'variant_id': x[field_id] if x.attribute_names else None,
                     'product_id': x['product_tmpl_id']['id'],
                     'stock': x[stock_field]} for x in product_ids[cont-inc: cont] if x[stock_field] >= 0]

            print ("-- Evaluado. Tiempo: {} ".format(time.time() - mid_time))
            mid_time = time.time()
        if product_ids:
            if len(product_ids) == 1:
                sql = "delete from exportxml_object where product_id = {}".format(product_ids.id)
            else:
                sql = "delete from exportxml_object where product_id in {}".format(tuple(product_ids.ids))
            self._cr.execute(sql)
            self._cr.execute(sql_ir_config)
        self._cr.execute(sql_ir_config)
        sql_ir_config = "update ir_config_parameter set value = '{}' where key = 'last_call_export_xmlstock'".format(
            time_now_str)
        self._cr.execute(sql_ir_config)
        self._cr.commit()
        #icp.last_call_export_xmlstock = last_call

        str = "Fin para {} con inc= {}. Tiempo : {}".format(len(product_ids), inc, time.time() - start_time)
        print (str)
        return res

    def test_recursitivy_product(self):
        bom_ids = self.env['mrp.bom'].search([])
        product_ids = bom_ids.mapped('product_tmpl_id').mapped('product_variant_ids') | bom_ids.mapped('product_id') | bom_ids.mapped('bom_line_ids').mapped('product_id')
        error_ids = self.env['product.product']
        for product_id in product_ids:
            try:
                p_ids = self.env['exportxml.object'].insert_product_ids(product_ids)
                print ('{} OK '.format(product_id.display_name))
            except:
                error_ids |= product_id
                print ('Error en {}. Id {}'.product_id.display_name, product_id.id)
        print ("Errores: \n {}".format(error_ids.ids))


    def insert_product_ids(self, list_product_ids=[], model=False):

        if not list_product_ids:
            return self.env['product.product']

        #print ('\n#######################\nSe van a añadir {} productos de {} al listado de stock'.format(len(list_product_ids), model))
        start_time = time.time()
        vals = ''
        list_product_ids |= self.env['mrp.bom'].export_related_bom_ids(list_product_ids)
        if not model:
            return list_product_ids


        for product_id in list_product_ids:
            vals = "{},({}, '{}')".format(vals, product_id.id, model)
        vals = vals[1:]
        sql = 'insert into exportxml_object ("product_id", "model") values {} on conflict ("product_id") do nothing'.format(vals)
        self._cr.execute(sql)
        print('---- Tiempo escritura {}'.format(time.time() - start_time))
        return True

class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    def insert_product_ids(self):
        product_ids = self
        if product_ids:
            self.env['exportxml.object'].insert_product_ids(product_ids.ids, self._name)
        return product_ids
