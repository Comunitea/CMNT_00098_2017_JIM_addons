# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product ean generator ",
    "version": "14.0.1.0.0",
    "depends": [
        "product",
    ],
    "author": "Comunitea",
    "license": "AGPL-3",
    "summary": """Set ean code from last""",
    "website": "http://www.comunitea.com",
    "data": [
        "views/product_template.xml",
        "views/ir_sequence.xml",
        "data/ean_sequence.xml",
    ],
    "installable": True,
    "auto_install": False,
}
