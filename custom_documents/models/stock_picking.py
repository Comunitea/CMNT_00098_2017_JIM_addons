# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import timedelta
from pytz import timezone


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    neutral_document = fields.Boolean('Neutral Document',
                                      related='sale_id.neutral_document')
    operator = fields.Char('Operator')
    same_day_delivery = fields.Boolean(compute='_compute_same_day_delivery')
    delivery_date = fields.Char(compute='_compute_delivery_date')

    @api.depends('date_done')
    # Si el albaran  se finalizó antes de las 17:30 entre semana se envía el
    # mismo día.
    def _compute_same_day_delivery(self):
        self.ensure_one()
        if self.date_done:
            same_day_delivery = True
            date_done = fields.Datetime.from_string(self.date_done)\
                .replace(tzinfo=timezone('Etc/UTC'))\
                .astimezone(timezone(self._context['tz']))
            if date_done.hour > 17 or \
                    (date_done.hour == 17 and date_done.minute > 30) or \
                    date_done.isoweekday() in (6, 7):
                same_day_delivery = False
            self.same_day_delivery = same_day_delivery

    @api.depends('date_done')
    def _compute_delivery_date(self):
        # Si no se envía el mismo día se comprueba que el día de envío no
        # sea ni sabado ni domingo
        self.ensure_one()
        if self.date_done:
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
