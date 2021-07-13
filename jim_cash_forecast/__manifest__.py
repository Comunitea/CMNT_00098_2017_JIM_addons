# © 2018 Comunitea - Santi Argüeso <santi@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Jim Cash Forecast",
    "version": "11.0.1.0.0",
    "author": "Comunitea ",
    "category": "Custom",
    "license": "AGPL-3",
    "depends": [
        "account",
        "purchase_advance_payment_forecast",
        "account_payment_order",
    ],
    "contributors": [
        "Comunitea ",
        "Santi Argüeso <santi@comunitea.com>",
    ],
    "data": [
        "views/cash_forecast_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
