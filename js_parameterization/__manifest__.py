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
        "data/b2b_out.xml",
        "views/parameterization.xml",
        "views/product.xml",
        "views/assets.xml"
    ],
    "depends": [
        "base",
        "stock",
        "product",
        "js_b2b"
    ],
    "installable": True
}
