# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)


class CarrierFile(models.Model):
    _inherit = 'delivery.carrier.file'

    printer_id = fields.Many2one('printing.printer', string='printer')
