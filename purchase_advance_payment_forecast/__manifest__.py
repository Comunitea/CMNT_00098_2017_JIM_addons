# -*- coding: utf-8 -*-
# Copyright 2018 Santi Argüeso, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Advance Payment Forecast",
    "version": "10.0.1.0.0",
    "author": "Comunitea",
    'website': 'www.comunitea.com',
    "category": "Purchases",
    "description": """Allow to create a  forecast account move when creating 
    advance payments on purchases """,
    "depends": ["purchase","account_forecast"],
    "data": ['views/payment_view.xml'
             ],
    "installable": True,
}
