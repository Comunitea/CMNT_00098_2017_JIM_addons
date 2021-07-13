# Copyright 2017 Kiko Sánchez<kiko@xcomunitea.com>.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Fixed rate for res.currency",
    "description": """ Permit convert currency with fix rate if in context
                    """,
    "version": "11.0.1.0.0",
    "author": "Comunitea ",
    "category": "Currency",
    "license": "AGPL-3",
    "depends": [
        "account",
        "jim_purchase",
        "purchase_advance_payment",
        "web_readonly_bypass",
    ],
    "contributors": [
        "Comunitea ",
    ],
    "data": [
        "views/account_payment.xml",
        "views/purchase_order.xml",
        "wizard/purchase_advance_payment_wzd.xml",
    ],
    "installable": True,
}
