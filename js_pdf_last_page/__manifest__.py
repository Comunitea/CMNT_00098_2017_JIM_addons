{
    "name": "JS PDF Last Page",
    "summary": "Permite añadir una última página HTML a los documentos PDF por tipo de informe y compañía",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Jim Sports",
    "category": "Document Management",
    "website": "https://jimsports.com",
    "depends": ["base", "custom_documents"],
    "data": [
        "security/ir.model.access.csv",
        "views/last_page.xml",
        "views/res_company.xml",
        "views/res_users_view.xml",
    ],
    "installable": True,
}
