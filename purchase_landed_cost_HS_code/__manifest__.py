# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Add Taxes form HS Codes to landed cost",
    "summary": "",
    "version": "10.0.1.0.0",
    "category": "Uncategorized",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "purchase_landed_cost",
        "product_harmonized_system"
    ],
    "data": [
        "views/purchase_cost_distribution_view.xml"
    ],
}
