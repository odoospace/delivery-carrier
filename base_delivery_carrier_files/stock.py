# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models, api
from odoo.tools.float_utils import float_compare, float_round
from datetime import date, datetime
from dateutil import relativedelta
import json
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT



class stock_picking(models.Model):
    _inherit = 'stock.picking'

    
    carrier_file_generated = fields.Boolean('Carrier File Generated',readonly=True, help="The file for the delivery carrier has been generated.")
    

    def generate_carrier_files(self, cr, uid, ids, auto=True,
                               recreate=False, context=None):
        """
        Generates all the files for a list of pickings according to
        their configuration carrier file.
        Does nothing on pickings without carrier or without
        carrier file configuration.
        Generate files only for outgoing pickings.

        :param list ids: list of ids of pickings for which we need a file
        :param auto: specify if we call the method from an automatic action
                     (on process on picking as instance)
                     or called manually from the wizard. When auto is True,
                     only the carrier files set as "auto_export"
                     are exported
        :return: True if successful
        """
        carrier_file_obj = self.pool.get('delivery.carrier.file')
        carrier_file_ids = {}
        for picking in self.browse(cr, uid, ids, context):
            print (picking[0])
            # if picking.stock_picking_type:
            #     picking_obj = self.pool.get('stock.picking.type')
            #     picking_type = picking_obj.browse(cr, uid, picking.stock_picking_type, context)
            #         if picking_type.code != 'outgoing':
            #             continue
            if not recreate and picking.carrier_file_generated:
                continue
            carrier = picking.carrier_id
            if not carrier or not carrier.carrier_file_id:
                continue
            if auto and not carrier.carrier_file_id.auto_export:
                continue
            p_carrier_file_id = picking.carrier_id.carrier_file_id.id
            carrier_file_ids.setdefault(p_carrier_file_id, []).\
                append(picking.id)

        for carrier_file_id, carrier_picking_ids\
                in carrier_file_ids.iteritems():
            carrier_file_obj.generate_files(cr, uid, carrier_file_id,
                                            carrier_picking_ids,
                                            context=context)
        return True

    def action_done(self, cr, uid, ids, context=None):
        result = super(stock_picking, self).action_done(cr, uid, ids,
                                                        context=context)
        self.generate_carrier_files(cr, uid, ids, auto=True, context=context)
        return result

    def do_transfer(self, cr, uid, ids, context=None):
        result = super(stock_picking, self).do_transfer(cr, uid, ids,
                                                        context=context)
        self.generate_carrier_files(cr, uid, ids, auto=True, context=context)
        return result
