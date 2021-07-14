# Copyright 2018 Santi Argüeso, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Forecast",
    "version": "12.0.1.0.0",
    "depends": [
        "account",
        "purchase_advance_payment",
    ],
    "author": "Comunitea",
    "license": "AGPL-3",
    "summary": """Documentary credit customization""",
    "website": "http://www.comunitea.com",
    "data": [
        "data/account_data.xml",
        "views/account_move_view.xml",
        "views/company_view.xml",
    ],
    "depends": ["account_due_list_check_received"],
    "installable": True,
    "auto_install": False,
}
