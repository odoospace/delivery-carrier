# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import upsrest


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
            if 'UPS WS' in self.carrier_id.name:
                d = upsrest.UPSAPI(
                    self.carrier_id.carrier_file_id.ups_api_username,
                    self.carrier_id.carrier_file_id.ups_api_password,
                    self.carrier_id.carrier_file_id.ups_api_license,
                    'prod'
                    )
                if self.number_of_packages == 1:
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
                                    "AddressLine": self.partner_id.street + ' ' + self.partner_id.street ,
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
                        }, 
                        "LabelSpecification": {
                            "LabelImageFormat": {
                                "Code": "PNG",
                                "Description": "PNG" 
                            },
                            "HTTPUserAgent": "Mozilla/4.5"
                        }
                    }
                    if self.carrier_id.carrier_file_id.ups_cod == True:
                        if self.sale_id:  
                            data["Shipment"]["ShipmentServiceOptions"] = {
                                "COD": {
                                    "CODFundsCode": "1",
                                    "CODAmount":{
                                        "CurrencyCode": "EUR",
                                        "MonetaryValue": self.sale_id.amount_total,
                                    }
                                }
                            },
                        else:
                            raise exceptions.Warning(("UPS API ERROR: The shipment type is COD but no sale was found" ))
                    
                        
                        
                    res = d.ship_with_data(data)

                    if 'Fault' in res:
                        raise exceptions.Warning(("DHL API ERROR: %s" % (res)))
                        return
                    else:
                        #save attachment
                        attachment = {}
                        attachment['name'] = res['ShipmentResponse']['ShipmentResults']['ShipmentIdentificationNumber']
                        attachment['datas_fname'] = attachment['name'] + '.pdf'
                        attachment['res_model'] = 'stock.picking'
                        attachment['res_id'] = self.id
                        attachment['datas'] = res['ShipmentResponse']['ShipmentResults']['PackageResults']['ShippingLabel']['GraphicImage']
                        attachment['file_type'] ='application/pdf'
                        att = self.env['ir.attachment'].create(attachment)

                    print res
                    self.carrier_file_generated = True
                    self.carrier_tracking_ref = res['ShipmentResponse']['ShipmentResults']['ShipmentIdentificationNumber']
                else:
                    raise exceptions.Warning(("UPS API ERROR: You must set a number of packages = 1"))
        result = super(stock_picking, self).action_done()
        return result

    @api.multi
    def do_transfer(self):
        if self.carrier_id:
            if 'UPS WS' in self.carrier_id.name:
                d = upsrest.UPSAPI(
                    self.carrier_id.carrier_file_id.ups_api_username,
                    self.carrier_id.carrier_file_id.ups_api_password,
                    self.carrier_id.carrier_file_id.ups_api_license,
                    'prod'
                    )
                if self.number_of_packages == 1:
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
                                    "Number": self.partner_id.phone or self.partner_id.movile
                                }, 
                                "Address": {
                                    "AddressLine": self.partner_id.street + ' ' + self.partner_id.street ,
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
                        }, 
                        "LabelSpecification": {
                            "LabelImageFormat": {
                                "Code": "PNG",
                                "Description": "PNG" 
                            },
                            "HTTPUserAgent": "Mozilla/4.5"
                        }
                    }
                    if self.carrier_id.carrier_file_id.ups_cod == True:
                        if self.sale_id:  
                            data["Shipment"]["ShipmentServiceOptions"] = {
                                "COD": {
                                    "CODFundsCode": "1",
                                    "CODAmount":{
                                        "CurrencyCode": "EUR",
                                        "MonetaryValue": self.sale_id.amount_total,
                                    }
                                }
                            },
                        else:
                            raise exceptions.Warning(("UPS API ERROR: The shipment type is COD but no sale was found" ))
                    
                    res = d.ship_with_data(data)

                    if 'Fault' in res:
                        raise exceptions.Warning(("DHL API ERROR: %s" % (res)))
                        return
                    else:
                        #save attachment
                        attachment = {}
                        attachment['name'] = res['ShipmentResponse']['ShipmentResults']['ShipmentIdentificationNumber']
                        attachment['datas_fname'] = attachment['name'] + '.pdf'
                        attachment['res_model'] = 'stock.picking'
                        attachment['res_id'] = self.id
                        attachment['datas'] = res['ShipmentResponse']['ShipmentResults']['PackageResults']['ShippingLabel']['HTMLImage']
                        attachment['file_type'] ='application/pdf'
                        att = self.env['ir.attachment'].create(attachment)

                    print res
                    self.carrier_file_generated = True
                    self.carrier_tracking_ref = res['ShipmentResponse']['ShipmentResults']['ShipmentIdentificationNumber']
                else:
                    raise exceptions.Warning(("UPS API ERROR: You must set a number of packages = 1"))
        result = super(stock_picking, self).do_transfer()

        return result
