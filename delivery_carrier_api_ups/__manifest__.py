# -*- coding: utf-8 -*-

{
    'name': 'Delivery Carrier API: UPS',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse',
    'description': """
Sub-module for Base Delivery Carrier Files.

Definition of the delivery carrier api for "UPS".

    """,
    'author': 'Impulzia S.L',
    'license': 'AGPL-3',
    'website': 'http://www.impulzia.com',
    'version': '9.0.0.1',
    'depends': ['base_delivery_carrier_files', 'stock', 'delivery_carrier_printer'],
    'init_xml': [],
    'data': ['views/carrier_file_view.xml'],
    'images': [],
    'installable': True,
    'auto_install': False,
}
