# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class AccountPayment(models.Model):

    inherit="account.payment"

