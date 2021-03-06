# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import upsrest
from base64 import b64decode, encodestring
import subprocess
import tempfile
import pdfkit
import io
from PIL import Image
import logging

_logger = logging.getLogger(__name__)


class CarrierFile(models.Model):
    _inherit = 'delivery.carrier.file'

    @api.model
    def get_type_selection(self):
        result = super(CarrierFile, self).get_type_selection()
        if 'UPS' not in result:
            result.append(('UPS', 'Envíos UPS-API'))
        return result

    type = fields.Selection(get_type_selection, 'Type', required=True)
    ups_cod = fields.Boolean(string='COD', default=False)
    ups_packet_service = fields.Char(string='Packet Service')
    ups_packet_service_description = fields.Char(string='Packet Service description')
    ups_api_username = fields.Char('Ups api Account ID')
    ups_api_password = fields.Char('Ups api KEY')
    ups_api_license = fields.Char('Ups api license')
    ups_api_url = fields.Char('Ups api URL')


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        if self.carrier_id:
            if 'UPS WS' in self.carrier_id.name and not self.carrier_tracking_ref:
                self.carrier_tracking_ref = 'GENERATING...'
                self._cr.commit()
                _logger.info('*** Connecting to UPS WS API %s %s' % (self.name, self.sale_id.name))
                d = upsrest.UPSAPI(
                    self.carrier_id.carrier_file_id.ups_api_username,
                    self.carrier_id.carrier_file_id.ups_api_password,
                    self.carrier_id.carrier_file_id.ups_api_license,
                    'prod'
                    )
                street = ''
                if self.partner_id.street:
                    street = self.partner_id.street
                if self.partner_id.street2:
                    street += ' ' + self.partner_id.street2
                data = {
                    "Request": {
                        "RequestOption": "validate",
                        "TransactionReference": {
                            "CustomerContext": "Your Customer Context"
                        }
                    },
                    "Shipment": {
                        "Description": "Description",
                        "Shipper": {
                            "Name": "Motoscoot",
                            "TaxIdentificationNumber": "ESB17990755", 
                            "Phone": {
                                "Number": "+34972413880",
                            },
                            "ShipperNumber": self.carrier_id.carrier_file_id.ups_api_username,
                            "Address": {
                                "AddressLine": "Can Pau Birol, 3-5",
                                "City": "Girona",
                                "PostalCode": "17005",
                                "CountryCode": "ES"
                            }
                        },
                        "ShipTo": {
                            "Name": self.partner_id.name,
                            "Phone": {
                                "Number": self.partner_id.phone or self.partner_id.mobile
                            }, 
                            "Address": {
                                "AddressLine": [street[0:35], street[35:70], street[70:105]],
                                "City": self.partner_id.city,
                                "PostalCode": self.partner_id.zip,
                                "CountryCode": self.partner_id.country_id.code
                            }
                        },
                        "ShipFrom": {
                            "Name": "Motoscoot",
                            "Phone": {
                                "Number": "+34972413880"
                            },
                            "Address": {
                                "AddressLine": "Can Pau Birol, 3-5",
                                "City": "Girona",
                                "PostalCode": "17005",
                                "CountryCode": "ES"
                            }
                        },
                        "PaymentInformation": {
                            "ShipmentCharge": {
                                "Type": "01",
                                "BillShipper": {
                                    "AccountNumber": self.carrier_id.carrier_file_id.ups_api_username
                                }
                            }
                        },
                        "Service": {
                            "Code": self.carrier_id.carrier_file_id.ups_packet_service,
                            "Description": self.carrier_id.carrier_file_id.ups_packet_service_description
                        },
                        "Package": {
                            "Description": "Box",
                            "Packaging": {
                                "Code": "02",
                                "Description": "Description"
                            },
                            "PackageWeight": {
                               "UnitOfMeasurement": {
                                   "Code": "KGS",
                                   "Description": "Kilograms"
                               },
                               "Weight": "1"
                            },
                        },
                        "ShipmentRatingOptions":{
                            "NegotiatedRatesIndicator": ""
                        },
                        "ShipmentServiceOptions":{
                            "Notification":{
                                "NotificationCode":"6",
                                "EMail":{
                                    "EMailAddress":self.partner_id.email
                                }
                            }
                        },
                        "ReferenceNumber":{
                            "Value": self.name
                        }
                    }, 
                    "LabelSpecification": {
                        "LabelImageFormat": {
                            "Code": "PNG",
                            "Description": "PNG" 
                        },
                        "HTTPUserAgent": "Mozilla/4.5"
                    }
                }
                if self.sale_id:
                    if self.carrier_id.carrier_file_id.ups_cod == True or self.sale_id.payment_mode_id.id == 4:  
                        data["Shipment"]["ShipmentServiceOptions"] = {
                            "COD": {
                                "CODFundsCode": "1",
                                "CODAmount":{
                                    "CurrencyCode": "EUR",
                                    "MonetaryValue": str(self.sale_id.amount_total),
                                }
                            }
                        },
                    # else:
                    #     raise exceptions.Warning(("UPS API ERROR: The shipment type is COD but no sale was found" ))
                
                res = d.ship_with_data(data)

                if 'Fault' in res:
                    raise exceptions.Warning(("UPS API ERROR: %s" % (res)))
                    return
                else:
                    _logger.info('*** UPS WS API Response OK')
                    src_label = res['ShipmentResponse']['ShipmentResults']['PackageResults']['ShippingLabel']['GraphicImage']
                    buf = io.BytesIO()
                    img = Image.open(io.BytesIO(b64decode(src_label))).transpose(Image.ROTATE_270)
                    img.save(buf, format='PNG')
                    pdf_label = buf.getvalue() 

                    f = tempfile.NamedTemporaryFile(delete=False)
                    f.write(pdf_label)
                    f.close()
                    printing_server = '%s:%d' % (self.carrier_id.carrier_file_id.printer_id.server_id.address, self.carrier_id.carrier_file_id.printer_id.server_id.port)
                    subprocess.call(['lp', '-h', printing_server, '-d', self.carrier_id.carrier_file_id.printer_id.system_name,f.name], shell=False)

                    if self.carrier_id.carrier_file_id.ups_cod == True:
                        src_label = res['ShipmentResponse']['ShipmentResults']['CODTurnInPage']['Image']['GraphicImage']
                        pdf_label = pdfkit.from_string(b64decode(src_label), False)

                        f = tempfile.NamedTemporaryFile(delete=False)
                        f.write(pdf_label)
                        f.close()
                        subprocess.call(['lp', '-h', printing_server, '-d', 'SAMSUNG', f.name], shell=False)

                self.carrier_file_generated = True
                self.carrier_tracking_ref = res['ShipmentResponse']['ShipmentResults']['ShipmentIdentificationNumber']
                _logger.info('*** UPS WS API Tracking added: %s' % self.carrier_tracking_ref)
                self._cr.commit()

        self._cr.commit()
        result = super(stock_picking, self).action_done()
        return result

    @api.multi
    def do_transfer(self):
        if self.carrier_id:
            if 'UPS WS' in self.carrier_id.name and not self.carrier_tracking_ref:
                self.carrier_tracking_ref = 'GENERATING...'
                self._cr.commit()
                _logger.info('*** Connecting to UPS WS API %s %s' % (self.name, self.sale_id.name))
                d = upsrest.UPSAPI(
                    self.carrier_id.carrier_file_id.ups_api_username,
                    self.carrier_id.carrier_file_id.ups_api_password,
                    self.carrier_id.carrier_file_id.ups_api_license,
                    'prod'
                    )
                street = ''
                if self.partner_id.street:
                    street = self.partner_id.street
                if self.partner_id.street2:
                    street += ' ' + self.partner_id.street2
                data = {
                    "Request": {
                        "RequestOption": "validate",
                        "TransactionReference": {
                            "CustomerContext": "Your Customer Context"
                        }
                    },
                    "Shipment": {
                        "Description": "Description",
                        "Shipper": {
                            "Name": "Motoscoot",
                            "TaxIdentificationNumber": "ESB17990755", 
                            "Phone": {
                                "Number": "+34972413880",
                            },
                            "ShipperNumber": self.carrier_id.carrier_file_id.ups_api_username,
                            "Address": {
                                "AddressLine": "Can Pau Birol, 3-5",
                                "City": "Girona",
                                "PostalCode": "17005",
                                "CountryCode": "ES"
                            }
                        },
                        "ShipTo": {
                            "Name": self.partner_id.name,
                            "Phone": {
                                "Number": self.partner_id.phone or self.partner_id.mobile
                            }, 
                            "Address": {
                                "AddressLine": [street[0:35], street[35:70], street[70:105]],
                                "City": self.partner_id.city,
                                "PostalCode": self.partner_id.zip,
                                "CountryCode": self.partner_id.country_id.code
                            }
                        },
                        "ShipFrom": {
                            "Name": "Motoscoot",
                            "Phone": {
                                "Number": "+34972413880"
                            },
                            "Address": {
                                "AddressLine": "Can Pau Birol, 3-5",
                                "City": "Girona",
                                "PostalCode": "17005",
                                "CountryCode": "ES"
                            }
                        },
                        "PaymentInformation": {
                            "ShipmentCharge": {
                                "Type": "01",
                                "BillShipper": {
                                    "AccountNumber": self.carrier_id.carrier_file_id.ups_api_username
                                }
                            }
                        },
                        "Service": {
                            "Code": self.carrier_id.carrier_file_id.ups_packet_service,
                            "Description": self.carrier_id.carrier_file_id.ups_packet_service_description
                        },
                        "Package": {
                            "Description": "Box",
                            "Packaging": {
                                "Code": "02",
                                "Description": "Description"
                            },
                            "PackageWeight": {
                               "UnitOfMeasurement": {
                                   "Code": "KGS",
                                   "Description": "Kilograms"
                               },
                               "Weight": "1"
                            },
                        },
                        "ShipmentRatingOptions":{
                            "NegotiatedRatesIndicator": ""
                        },
                        "ShipmentServiceOptions":{
                            "Notification":{
                                "NotificationCode":"6",
                                "EMail":{
                                    "EMailAddress":self.partner_id.email
                                }
                            }
                        },
                        "ReferenceNumber":{
                            "Value": self.name
                        }
                    }, 
                    "LabelSpecification": {
                        "LabelImageFormat": {
                            "Code": "PNG",
                            "Description": "PNG" 
                        },
                        "HTTPUserAgent": "Mozilla/4.5"
                    }
                }
                if self.sale_id:
                    if self.carrier_id.carrier_file_id.ups_cod == True or self.sale_id.payment_mode_id.id == 4:    
                        data["Shipment"]["ShipmentServiceOptions"] = {
                            "COD": {
                                "CODFundsCode": "1",
                                "CODAmount":{
                                    "CurrencyCode": "EUR",
                                    "MonetaryValue": str(self.sale_id.amount_total),
                                }
                            }
                        },
                    # else:
                    #     raise exceptions.Warning(("UPS API ERROR: The shipment type is COD but no sale was found" ))
                
                res = d.ship_with_data(data)

                if 'Fault' in res:
                    raise exceptions.Warning(("UPS API ERROR: %s" % (res)))
                    return
                else:
                    _logger.info('*** UPS WS API Response OK')
                    src_label = res['ShipmentResponse']['ShipmentResults']['PackageResults']['ShippingLabel']['GraphicImage']
                    buf = io.BytesIO()
                    img = Image.open(io.BytesIO(b64decode(src_label))).transpose(Image.ROTATE_270)
                    img.save(buf, format='PNG')
                    pdf_label = buf.getvalue() 

                    f = tempfile.NamedTemporaryFile(delete=False)
                    f.write(pdf_label)
                    f.close()
                    printing_server = '%s:%d' % (self.carrier_id.carrier_file_id.printer_id.server_id.address, self.carrier_id.carrier_file_id.printer_id.server_id.port)
                    subprocess.call(['lp', '-h', printing_server, '-d', self.carrier_id.carrier_file_id.printer_id.system_name,f.name], shell=False)

                    if self.carrier_id.carrier_file_id.ups_cod == True:
                        src_label = res['ShipmentResponse']['ShipmentResults']['CODTurnInPage']['Image']['GraphicImage']
                        pdf_label = pdfkit.from_string(b64decode(src_label), False)

                        f = tempfile.NamedTemporaryFile(delete=False)
                        f.write(pdf_label)
                        f.close()
                        subprocess.call(['lp', '-h', printing_server, '-d', 'SAMSUNG', f.name], shell=False)

                self.carrier_file_generated = True
                self.carrier_tracking_ref = res['ShipmentResponse']['ShipmentResults']['ShipmentIdentificationNumber']
                _logger.info('*** UPS WS API Tracking added: %s' % self.carrier_tracking_ref)
                self._cr.commit()
        
        self._cr.commit()
        result = super(stock_picking, self).do_transfer()
        return result


    @api.multi
    def regenerate_ups_api(self):
        if self.carrier_id:
            if 'UPS WS' in self.carrier_id.name:
                self.carrier_tracking_ref = 'GENERATING...'
                self._cr.commit()
                _logger.info('*** Connecting to UPS WS API %s %s' % (self.name, self.sale_id.name))
                d = upsrest.UPSAPI(
                    self.carrier_id.carrier_file_id.ups_api_username,
                    self.carrier_id.carrier_file_id.ups_api_password,
                    self.carrier_id.carrier_file_id.ups_api_license,
                    'prod'
                    )
                street = ''
                if self.partner_id.street:
                    street = self.partner_id.street
                if self.partner_id.street2:
                    street += ' ' + self.partner_id.street2
                data = {
                    "Request": {
                        "RequestOption": "validate",
                        "TransactionReference": {
                            "CustomerContext": "Your Customer Context"
                        }
                    },
                    "Shipment": {
                        "Description": "Description",
                        "Shipper": {
                            "Name": "Motoscoot",
                            "TaxIdentificationNumber": "ESB17990755", 
                            "Phone": {
                                "Number": "+34972413880",
                            },
                            "ShipperNumber": self.carrier_id.carrier_file_id.ups_api_username,
                            "Address": {
                                "AddressLine": "Can Pau Birol, 3-5",
                                "City": "Girona",
                                "PostalCode": "17005",
                                "CountryCode": "ES"
                            }
                        },
                        "ShipTo": {
                            "Name": self.partner_id.name,
                            "Phone": {
                                "Number": self.partner_id.phone or self.partner_id.mobile
                            }, 
                            "Address": {
                                "AddressLine": [street[0:35], street[35:70], street[70:105]],
                                "City": self.partner_id.city,
                                "PostalCode": self.partner_id.zip,
                                "CountryCode": self.partner_id.country_id.code
                            }
                        },
                        "ShipFrom": {
                            "Name": "Motoscoot",
                            "Phone": {
                                "Number": "+34972413880"
                            },
                            "Address": {
                                "AddressLine": "Can Pau Birol, 3-5",
                                "City": "Girona",
                                "PostalCode": "17005",
                                "CountryCode": "ES"
                            }
                        },
                        "PaymentInformation": {
                            "ShipmentCharge": {
                                "Type": "01",
                                "BillShipper": {
                                    "AccountNumber": self.carrier_id.carrier_file_id.ups_api_username
                                }
                            }
                        },
                        "Service": {
                            "Code": self.carrier_id.carrier_file_id.ups_packet_service,
                            "Description": self.carrier_id.carrier_file_id.ups_packet_service_description
                        },
                        "Package": {
                            "Description": "Box",
                            "Packaging": {
                                "Code": "02",
                                "Description": "Description"
                            },
                            "PackageWeight": {
                               "UnitOfMeasurement": {
                                   "Code": "KGS",
                                   "Description": "Kilograms"
                               },
                               "Weight": "1"
                            },
                        },
                        "ShipmentRatingOptions":{
                            "NegotiatedRatesIndicator": ""
                        },
                        "ShipmentServiceOptions":{
                            "Notification":{
                                "NotificationCode":"6",
                                "EMail":{
                                    "EMailAddress":self.partner_id.email
                                }
                            }
                        },
                        "ReferenceNumber":{
                            "Value": self.name
                        }
                    }, 
                    "LabelSpecification": {
                        "LabelImageFormat": {
                            "Code": "PNG",
                            "Description": "PNG" 
                        },
                        "HTTPUserAgent": "Mozilla/4.5"
                    }
                }
                if self.sale_id:
                    if self.carrier_id.carrier_file_id.ups_cod == True or self.sale_id.payment_mode_id.id == 4:  
                        data["Shipment"]["ShipmentServiceOptions"] = {
                            "COD": {
                                "CODFundsCode": "1",
                                "CODAmount":{
                                    "CurrencyCode": "EUR",
                                    "MonetaryValue": str(self.sale_id.amount_total),
                                }
                            }
                        },
                    # else:
                    #     raise exceptions.Warning(("UPS API ERROR: The shipment type is COD but no sale was found" ))
                
                res = d.ship_with_data(data)

                if 'Fault' in res:
                    raise exceptions.Warning(("UPS API ERROR: %s" % (res)))
                    return
                else:
                    _logger.info('*** UPS WS API Response OK')
                    src_label = res['ShipmentResponse']['ShipmentResults']['PackageResults']['ShippingLabel']['GraphicImage']
                    buf = io.BytesIO()
                    img = Image.open(io.BytesIO(b64decode(src_label))).transpose(Image.ROTATE_270)
                    img.save(buf, format='PNG')
                    pdf_label = buf.getvalue() 

                    f = tempfile.NamedTemporaryFile(delete=False)
                    f.write(pdf_label)
                    f.close()
                    printing_server = '%s:%d' % (self.carrier_id.carrier_file_id.printer_id.server_id.address, self.carrier_id.carrier_file_id.printer_id.server_id.port)
                    subprocess.call(['lp', '-h', printing_server, '-d', self.carrier_id.carrier_file_id.printer_id.system_name,f.name], shell=False)

                    if self.carrier_id.carrier_file_id.ups_cod == True:
                        src_label = res['ShipmentResponse']['ShipmentResults']['CODTurnInPage']['Image']['GraphicImage']
                        pdf_label = pdfkit.from_string(b64decode(src_label), False)

                        f = tempfile.NamedTemporaryFile(delete=False)
                        f.write(pdf_label)
                        f.close()
                        subprocess.call(['lp', '-h', printing_server, '-d', 'SAMSUNG', f.name], shell=False)

                self.carrier_file_generated = True
                self.carrier_tracking_ref = res['ShipmentResponse']['ShipmentResults']['ShipmentIdentificationNumber']
                _logger.info('*** UPS WS API Tracking added: %s' % self.carrier_tracking_ref)
                self._cr.commit()
        
        self._cr.commit()
        return 
