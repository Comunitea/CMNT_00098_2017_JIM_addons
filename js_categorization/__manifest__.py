{
    "name": "JS Categorization",
    "summary": "Añade una pestaña de categorización en los productos/variantes",
    "version": "10.0.2.0",
    "license": "AGPL-3",
    "author": "Jim Sports",
    "category": "Inventory",
    "website": "https://jimsports.com",
    "depends": [
        "base",
        "stock",
        "product"
    ],
    "data": [
        "security/res.groups.xml",
        "security/ir.model.access.csv",
        "views/categorization.xml",
        "views/product.xml",
        "views/assets.xml",
        "wizards/select_variant_wizard_view.xml"
    ],
    "installable": True
}
