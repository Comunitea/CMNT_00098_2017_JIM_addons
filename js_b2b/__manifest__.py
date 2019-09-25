# -*- coding: utf-8 -*-
# © 2019 Jim Sports Group
{
    'name': 'JS B2B',
    'version': '10.0.1.0',
    'author': 'Jim Sports',
    'category': 'Connector',
    'website': 'https://jimsports.com',
    'description': 'Conector para sincronizar datos con otras plataformas/clientes',
    'license': 'AGPL-3',
    'qweb': [
        'static/xml/widgets.xml',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/client.xml',
        'views/item.xml',
        'views/assets.xml'
    ],
    'depends': [
        'base',
        'jim_sale',
        'product_tags',
        'purchase',
        'sga_file',
        'product_code_generator'
    ],
    'contributors': [
        "Pablo Luaces <pablo@jimsports.com>"
    ],
    "application": False,
    "installable": True
}