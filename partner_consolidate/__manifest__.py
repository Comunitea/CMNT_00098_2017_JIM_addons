# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Partner Consolidate",
    "version": "14.0.1.0.0",
    "author": "Comunitea ",
    "category": "Custom",
    "license": "AGPL-3",
    "depends": ["base", "account_payment_partner", "account"],
    "contributors": [
        "Comunitea ",
    ],
    "data": [
        "views/partner_view.xml",
        "views/account_view.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "installable": True,
}
