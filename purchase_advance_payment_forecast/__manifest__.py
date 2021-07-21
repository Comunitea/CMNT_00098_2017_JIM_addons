# Copyright 2018 Santi Argüeso, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Advance Payment Forecast",
    "version": "14.0.1.0.0",
    "author": "Comunitea",
    "website": "www.comunitea.com",
    "category": "Purchases",
    "description": """Allow to create a  forecast account move when creating 
    advance payments on purchases """,
    "depends": [
        "purchase",
        "account_forecast",
        "account_due_list_check_received",
    ],
    "data": ["views/payment_view.xml"],
    "installable": True,
}
