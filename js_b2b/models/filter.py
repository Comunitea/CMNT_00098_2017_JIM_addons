# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from ..base.helper import JSync

class B2bFilters(models.Model):
    _name = 'b2b.filter'
    _description = "B2B Filter"

    client = fields.Many2one('b2b.client', 'B2B Client', ondelete='cascade', required=True, help="Select client")
    item = fields.Many2one('b2b.item', 'B2B Item', ondelete='cascade', required=True, help="Select item", domain="[('id','=',0)]")
    where = fields.Text('Filter', required=True, default='[]', help="Write your filter here in polish notation")

    @api.onchange('client')
    def _onchange_client(self):
        return { 'domain': { 'item' : [('id', 'in', self.client.items.ids if self.client else [])] }}

    def __b2b_record(self, mode='create', vals=None):  
        jfilter = JSync(self.id)
        # Set data
        jfilter.obj_type = 'client'
        jfilter.obj_data = {
            'client': self.client.id,
            'item': self.item.id,
            'filter': self.where
        }
        # Filter data
        jfilter.filter_obj_data(vals)
        # Send item
        return jfilter.send('config', mode, 60)

    @api.model
    def create(self, vals):
        item = super(B2bItems, self).create(vals)
        item.__b2b_record('create', vals)
        return item

    @api.multi
    def write(self, vals):
        super(B2bItems, self).write(vals)
        for item in self:
           item.__b2b_record('update', vals)
        return True

    @api.multi
    def unlink(self):
        for item in self:
            item.__b2b_record('delete')
        super(B2bItems, self).unlink()
        return True