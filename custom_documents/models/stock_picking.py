# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import timedelta
from pytz import timezone


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    documento_neutro = fields.Boolean()
    operator = fields.Char()
    same_day_delivery = fields.Boolean(compute='_compute_same_day_delivery')
    delivery_date = fields.Char(compute='_compute_delivery_date')

    @api.depends('create_date', 'date_done')
    # Si el albaran  se creo antes de las 17:30 y se finalizó entre
    # semana se envía el mismo día.
    def _compute_same_day_delivery(self):
        self.ensure_one()
        if self.create_date and self.date_done:
            same_day_delivery = True
            create_date = fields.Datetime.from_string(self.create_date)\
                .replace(tzinfo=timezone('Etc/UTC'))\
                .astimezone(timezone(self._context['tz']))
            date_done = fields.Datetime.from_string(self.date_done)\
                .replace(tzinfo=timezone('Etc/UTC'))\
                .astimezone(timezone(self._context['tz']))
            if create_date.hour > 17 or \
                    (create_date.hour == 17 and create_date.minute > 30) or \
                    date_done.isoweekday() in (6, 7):
                same_day_delivery = False
            self.same_day_delivery = same_day_delivery

    @api.depends('create_date', 'date_done')
    def _compute_delivery_date(self):
        # Si no se envía el mismo día se comprueba que el día de envío no sea ni sabado ni domingo
        self.ensure_one()
        if self.date_done and self.create_date:
            if self.same_day_delivery:
                self.delivery_date = self.date_done
            else:
                date_done = fields.Datetime.from_string(self.date_done)
                next_date = date_done + timedelta(days=1)
                delivery_date = next_date
                if next_date.isoweekday() == 6:
                    delivery_date = next_date + timedelta(days=2)
                elif next_date.isoweekday() == 7:
                    delivery_date = next_date + timedelta(days=1)
                self.delivery_date = delivery_date
