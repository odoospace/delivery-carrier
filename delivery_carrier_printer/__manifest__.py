# -*- coding: utf-8 -*-

{
    'name': 'Delivery Carrier Printer Label',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse',
    'description': """
Add selectable printer for api integrations.

    """,
    'author': 'Impulzia S.L',
    'license': 'AGPL-3',
    'website': 'http://www.impulzia.com',
    'depends': ['base_delivery_carrier_label', 'stock'],
    'init_xml': [],
    'data': ['views/carrier_file_view.xml'],
    'images': [],
    'installable': True,
    'auto_install': False,
}
