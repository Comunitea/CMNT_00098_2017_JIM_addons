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
        "sale_margin",
        'delivery',
        'account_payment_sale',
        'stock_picking_invoice_link'
    ],
    "data": [
        'views/layout_templates.xml',
        'data/report_paperformat_data.xml',
        'views/sale_order_report.xml',
        'views/company.xml',
        'views/picking_grouped_invoice_report.xml',
        'report_invoice.xml'
    ],
}
