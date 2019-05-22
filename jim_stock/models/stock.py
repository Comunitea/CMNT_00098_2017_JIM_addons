# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
try:
    from unidecode import unidecode
except (ImportError, IOError) as err:
    _logger.debug(err)


class StockPicking (models.Model):
    _inherit = "stock.picking"

    pick_weight = fields.Float(string='Shipping Weight',
                 help="Manual weight in pick. Propagate to next asociated pick.")

    pick_packages = fields.Integer("Número de paquetes")
    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=1, default=lambda self: self.env.user.company_id.partner_id.id,
        states={})
    observations = fields.Text(related='sale_id.observations')
    purchase_date_order = fields.Datetime(related="purchase_id.date_order")
    confirmation_date = fields.Datetime(related="sale_id.confirmation_date")
    returned_picking_id = fields.Many2one('stock.picking')
    force_date = fields.Datetime('Forzar fecha de entrada')

    def _get_label_data(self):
        res = super(StockPicking, self)._get_label_data()
        if self.pick_packages <= 0:
            raise UserError(_('Please set the number of packages.'))
        res['total_bultos'] = self.pick_packages
        res['total_kilos'] = self.pick_weight
        res['peso_bulto'] = self.pick_weight
        res['cliente_atencion'] = self.partner_id.default_contact_person and \
            unidecode(self.partner_id.default_contact_person) or \
            unidecode(self.partner_id.name)
        return res

    @api.multi
    def action_done(self):
        create_date = self.force_date or time.strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        self_date_context = self.with_context(create_date=create_date)
        return super(StockPicking, self_date_context).action_done()

    @api.multi
    def do_transfer(self):
        create_date = self.force_date or time.strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        self_date_context = self.with_context(create_date=create_date)
        return super(StockPicking, self_date_context).do_transfer()


class StockLocation(models.Model):
    _inherit = "stock.location"

    deposit = fields.Boolean('Deposit')


class StockQuantPackage(models.Model):

    _inherit = "stock.quant.package"

    @api.depends('quant_ids', 'children_ids')
    def _compute_volume(self):
        volume = 0
        for quant in self.quant_ids:
            volume += quant.qty * quant.product_id.volume
        for pack in self.children_ids:
            pack._compute_volume()
            volume += pack.volume
        self.volume = volume

    @api.depends('height', 'width', 'length', 'volume')
    def _compute_package_volume(self):

        self.shipping_volume = (self.width * self.height * self.length) or self.volume

    packaging_id_code = fields.Char(related='packaging_id.shipper_package_code')
    height = fields.Float('Height')
    width = fields.Float('Width')
    length = fields.Float('Length')
    volume = fields.Float(compute='_compute_volume', digits=(10, 6))
    shipping_volume = fields.Float(string='Shipping Volume',
                                   compute="_compute_package_volume",
                                   digits=(10, 6))


class StockQuant(models.Model):

    _inherit = 'stock.quant'

    @api.model
    def create(self, vals):
        if self._context.get('create_date', False):
            vals['in_date'] = self._context['create_date']
        res = super(StockQuant, self).create(vals)
        if self._context.get('create_date', False):
            self.env.cr.execute("update stock_quant set create_date='%s' where id=%s" % (self._context['create_date'], res.id))
        return res


class StockMove(models.Model):

    _inherit = 'stock.move'

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        if self._context.get('create_date', False):
            self.env.cr.execute("update stock_move set create_date='%s' where id=%s" % (self._context['create_date'], res.id))
        return res

    @api.multi
    def action_done(self):
        res = super(StockMove, self).action_done()
        date = self._context.get('create_date', time.strftime(
            DEFAULT_SERVER_DATETIME_FORMAT))
        self.write({'date': date})
        return res
