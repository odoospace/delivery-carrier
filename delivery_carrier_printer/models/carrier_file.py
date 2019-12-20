# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)


class CarrierFile(models.Model):
    _inherit = 'carrier.account'

    printer_id = fields.Many2one('printing.printer', string='printer')
