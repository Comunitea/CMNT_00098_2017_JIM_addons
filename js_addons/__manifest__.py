{
    "name": "JS Addons",
    "summary": "Añade pequeñas funcionalidades a Odoo en diferentes modelos/vistas",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Jim Sports",
    "category": "Generic",
    "website": "https://jimsports.com",
    "depends": [
        "base",
        "product",
        "sale",
        "stock",
        "product_custom",
        "custom_sale_order_variant_mgmt",
        "telesale_manage_variants",
        "telesale",
    ],
    "data": ["views/assets.xml", "views/sale_views.xml", "views/product.xml"],
    "qweb": [
        "static/xml/popups_template.xml",
    ],
    "installable": True,
}
