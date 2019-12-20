# -*- coding: utf-8 -*-

{
    'name': 'Delivery Carrier API: DHL',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse',
    'description': """
Sub-module for Base Delivery Carrier Label.

Definition of the delivery carrier api for "DHL".

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
