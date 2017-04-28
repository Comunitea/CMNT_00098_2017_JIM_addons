# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Custom documents",
    "summary": "Report customizations",
    "version": "8.0.1.0.0",
    "category": "Uncategorized",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "report",
        "sale",
        "sale_stock",
        'delivery',
        'account_payment_sale'
    ],
    "data": [
        'views/layout_templates.xml',
        'views/sale_order_report.xml',
        'data/report_paperformat_data.xml',
        'views/company.xml'
    ],
}
