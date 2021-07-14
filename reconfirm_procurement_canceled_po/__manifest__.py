# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


{
    "name": "Reconfirm procurement in canceled po",
    "version": "12.0.1.0.0",
    "author": "Comunitea, ",
    "category": "",
    "license": "AGPL-3",
    "description": "Allow reconfirm procurement in purchase orders",
    "depends": ["purchase"],
    "contributors": ["Comunitea", "Kiko Sanchez<kiko@comunitea.com>"],
    "data": [
        "wizard/wzd_confirm_procurement.xml",
        #'security/ir.model.access.csv',
    ],
    "demo": [],
    "test": [],
    "installable": True,
}
