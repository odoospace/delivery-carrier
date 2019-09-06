# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import nacex
from datetime import datetime
import base64
import io
from PIL import Image
import subprocess
import tempfile
import pdfkit

import logging

_logger = logging.getLogger(__name__)


class CarrierFile(models.Model):
    _inherit = 'delivery.carrier.file'

    printer_id = fields.Many2one('printing.printer', string='printer')
