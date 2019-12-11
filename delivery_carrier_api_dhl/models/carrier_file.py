# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import dhl


class CarrierFile(models.Model):
    _inherit = 'delivery.carrier.file'

    @api.model
    def get_type_selection(self):
        result = super(CarrierFile, self).get_type_selection()
        if 'DHL' not in result:
            result.append(('DHL', 'Envíos DHL-API'))
        return result

    @api.model
    def _get_package(self):
        return (
            ('SMALL', 'SMALL'))

    @api.model
    def _get_service(self):
        return (
            ('5', 'COD_CASH'))

    type = fields.Selection(get_type_selection, 'Type', required=True)
    api_export = fields.Boolean('Usar API?', help="Si esta marcado se usara la API para obtener la etiqueta de envío")
    dhl_api_account = fields.Char('Dhl api Account ID')
    dhl_api_key = fields.Char('Dhl api KEY')
    dhl_api_user = fields.Char('Dhl api User')
    dhl_api_url = fields.Char('Dhl api URL')
    dhl_package_type = fields.Selection([('SMALL', 'SMALL')], 'Tipo de paquete', help="Escoge el tipo de paquete")
    dhl_service_level = fields.Selection([('5', 'COD_CASH')], 'Tipo de servicio', help="Tipo de servicio")
    dhl_description_goods = fields.Char('Descripcion mercancia', size=30)
    dhl_cash = fields.Boolean('Contrareembolso?', help="Marcar para contrareembolso")
    dhl_cod_price = fields.Float('Precio contrareembolso')
    dhl_mail_notification = fields.Char('Email Notificacion', size=120)


CarrierFile()


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        if self.carrier_id:
            if self.carrier_id.name == 'DHL API':
                d = dhl.API()
                if self.number_of_packages == 1:
                    data = {
                        "receiver": {
                            "email": self.partner_id.email,
                            "phoneNumber": self.partner_id.phone,
                            "name": {
                                "firstName": self.partner_id.name.split(' ')[0],
                                "companyName": self.partner_id.parent_id.name or self.partner_id.name,
                                "lastName": ''.join(e + ' ' for e in self.partner_id.name.split(' ')[1:]) or ''
                            },
                            "address": {
                                "countryCode": self.partner_id.country_id.code,
                                "number": "",
                                "isBusiness": True,
                                "street": self.partner_id.street,
                                "city": self.partner_id.city,
                                "postalCode": self.partner_id.zip
                            }
                        },
                        "shipper": {
                            "email": self.company_id.email,
                            "phoneNumber": self.company_id.phone,
                            "name": {
                                "firstName": self.company_id.name.split(' ')[0],
                                "lastName": ''.join(e + ' ' for e in self.company_id.name.split(' ')[1:]) or ''
                            },
                            "address": {
                                "street": self.company_id.street,
                                "city": self.company_id.city,
                                "number": "",
                                "postalCode": self.company_id.zip,
                                "isBusiness": True,
                                "addition": "A",
                                "countryCode": self.company_id.country_id.code
                            }
                        },
                        "parcelTypeKey": "SMALL",
                        "pieceNumber": 1,
                        "quantity": self.number_of_packages,
                        "automaticPrintDialog": False,
                        "returnLabel": False
                    }
                    data["options"] = [
                        {
                            "key": "DOOR"
                        },
                        {
                            "key": "REFERENCE",
                            "input": self.name
                        }
                    ]
                    if self.sale_id:  
                        if self.sale_id.payment_mode_id.id == 4 :
                            data["options"].append({   
                                "key": "COD_CASH",
                                "input": self.sale_id.amount_total
                            }) 
                    res = d.get_label(data)
                    if 'message' in res:
                        raise exceptions.Warning(("API ERROR: %s. \n %s. \n %s" % (res['details'], res['key'], res['message'])))
                        return
                    else:
                        #save attachment
                        attachment = {}
                        attachment['name'] = res['trackerCode']
                        attachment['datas_fname'] = attachment['name'] + '.pdf'
                        attachment['res_model'] = 'stock.picking'
                        attachment['res_id'] = self.id
                        attachment['datas'] = res['pdf']
                        attachment['file_type'] ='application/pdf'
                        att = self.env['ir.attachment'].create(attachment)

                    print res
                    self.carrier_file_generated = True
                    self.carrier_tracking_ref = res['trackerCode']
                else:
                    raise exceptions.Warning(("DHL API ERROR: You must set a number of packages = 1"))
        result = super(stock_picking, self).action_done()
        return result

    @api.multi
    def do_transfer(self):
        if self.carrier_id:
            if self.carrier_id.name == 'DHL API':
                d = dhl.API()
                if self.number_of_packages == 1:
                    data = {
                        "receiver": {
                            "email": self.partner_id.email,
                            "phoneNumber": self.partner_id.phone,
                            "name": {
                                "firstName": self.partner_id.name.split(' ')[0],
                                "companyName": self.partner_id.parent_id.name or self.partner_id.name,
                                "lastName": ''.join(e + ' ' for e in self.partner_id.name.split(' ')[1:]) or ''
                            },
                            "address": {
                                "countryCode": self.partner_id.country_id.code,
                                "number": "",
                                "isBusiness": True,
                                "street": self.partner_id.street,
                                "city": self.partner_id.city,
                                "postalCode": self.partner_id.zip
                            }
                        },
                        "shipper": {
                            "email": self.company_id.email,
                            "phoneNumber": self.company_id.phone,
                            "name": {
                                "firstName": self.company_id.name.split(' ')[0],
                                "lastName": ''.join(e + ' ' for e in self.company_id.name.split(' ')[1:]) or ''
                            },
                            "address": {
                                "street": self.company_id.street,
                                "city": self.company_id.city,
                                "number": "",
                                "postalCode": self.company_id.zip,
                                "isBusiness": True,
                                "addition": "A",
                                "countryCode": self.company_id.country_id.code
                            }
                        },
                        "parcelTypeKey": "SMALL",
                        "pieceNumber": 1,
                        "quantity": self.number_of_packages,
                        "automaticPrintDialog": False,
                        "returnLabel": False
                    }
                    data["options"] = [
                        {
                            "key": "DOOR"
                        },
                        {
                            "key": "REFERENCE",
                            "input": self.name
                        }
                    ]
                    if self.sale_id:  
                        if self.sale_id.payment_mode_id.id == 4 :
                            data["options"].append({   
                                "key": "COD_CASH",
                                "input": self.sale_id.amount_total
                            }) 
                    res = d.get_label(data)
                    if 'message' in res:
                        raise exceptions.Warning(("DHL API ERROR: %s. \n %s. \n %s" % (res['details'], res['key'], res['message'])))
                        return
                    else:
                        #save attachment
                        attachment = {}
                        attachment['name'] = res['trackerCode']
                        attachment['datas_fname'] = attachment['name'] + '.pdf'
                        attachment['res_model'] = 'stock.picking'
                        attachment['res_id'] = self.id
                        attachment['datas'] = res['pdf']
                        attachment['file_type'] ='application/pdf'
                        att = self.env['ir.attachment'].create(attachment)

                    print res
                    self.carrier_file_generated = True
                    self.carrier_tracking_ref = res['trackerCode']
                else:
                    raise exceptions.Warning(("DHL API ERROR: You must set a number of packages = 1"))
        result = super(stock_picking, self).do_transfer()

        return result
