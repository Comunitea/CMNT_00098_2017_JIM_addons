# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Export product to XLS",
    "version": "12.0.1.0.0",
    "author": "Comunitea",
    "website": "http://www.comunitea.com",
    "category": "Stock / Product",
    "depends": [
        "product",
        "jim_stock",
        "report_xlsx",
    ],
    "contributors": [
        "Kiko Sánchez <kiko@comunitea.com>",
    ],
    "external_dependencies": {
        "python": ["xlwt"],
    },
    "data": [
        "wizard/wzd_product_web_report.xml",
        "report/product_web_xls.xml",
        #'views/product_web_report.xml'
    ],
    "installable": True,
}
