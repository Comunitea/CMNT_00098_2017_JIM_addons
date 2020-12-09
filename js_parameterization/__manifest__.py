{
    "name": "JS Parameterization",
    "summary": "Añade una pestaña de parametrización en los productos/variantes",
    "version": "10.0.2.0",
    "license": "AGPL-3",
    "author": "Jim Sports",
    "category": "Inventory",
    "website": "https://jimsports.com",
    "data": [
        "security/res.groups.xml",
        "security/ir.model.access.csv",
        "views/parameterization.xml",
        "views/product.xml",
        "views/assets.xml",
        "wizards/select_variant_wizard_view.xml"
    ],
    "depends": [
        "base",
        "stock",
        "product"
    ],
    "installable": True
}
