# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product code generator (from attributes)",
    "version": "11.0.1.0.0",
    "depends": [
        "product",
    ],
    "author": "Comunitea",
    "license": "AGPL-3",
    "summary": """Set product.product default code from variant seq""",
    "website": "http://www.comunitea.com",
    "data": [
        "views/product_attribute.xml",
        "views/product_template.xml",
    ],
    "installable": True,
    "auto_install": False,
}
