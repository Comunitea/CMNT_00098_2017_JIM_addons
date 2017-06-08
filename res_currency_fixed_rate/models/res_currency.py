# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez<kiko@xcomunitea.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp



class Currency(models.Model):

    _inherit = "res.currency"

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency):
        fixed_rated = self._context.get("fixed_rate", False)
        if fixed_rated:
            return 1/fixed_rated
        else:
            return super(Currency, self)._get_conversion_rate(from_currency, to_currency)
