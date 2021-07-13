# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sequence en lineas de compras",
    "version": "11.0.1.0.0",
    "depends": ["purchase_order_variant_mgmt"],
    "author": "Comunitea",
    "license": "AGPL-3",
    "summary": """Sequencias en compras""",
    "website": "http://www.comunitea.com",
    "data": [
        "security/purchase_security.xml",
        #'views/product_product.xml',
        "views/product_manage_variant_view.xml",
        "views/purchase_order.xml",
        "views/res_config_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
