# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from ..base.helper import OutputHelper, Google
import json

class B2bController(http.Controller):
    @http.route([
        '/b2b_incoming'
    ], type='http', auth='user', methods=['GET',])
    def index(self, **kw):
        return "Allowed items: %s" % map(str, request.env['b2b.item.in'].search([]).mapped('name'))

    @http.route([
        '/b2b_incoming'
    ], type='json', auth='public', methods=['POST',])
    def message(self, **kw):
        env = request.env
        
        try:
            # Process message
            data_obj = http.request.params
            item_user = data_obj.get('user_id')
            item_name = data_obj.get('object')
            item_action = data_obj.get('action', 'create')
            item_data = data_obj.get('data')

            # Debug data
            debug_str = "[B2B INCOMING] Message: " \
                    "\n    - name: {}" \
                    "\n    - user: {}" \
                    "\n    - operation: {}" \
                    "\n    - data: {}".format(item_name, item_user, item_action, item_data)

            # Process item
            if env['b2b.item.in'].sudo().must_process(item_name, item_user, item_data, item_action):
                OutputHelper.print_message(debug_str, OutputHelper.INFO)
            else:
                # ERROR
                OutputHelper.print_message(debug_str, OutputHelper.ERROR)

        except ValueError:
            # Invalid JSON
            print("[PUBLIC-IN] Invalid JSON received: %s" % message.data)