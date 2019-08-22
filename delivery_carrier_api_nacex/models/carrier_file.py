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


class CarrierFile(models.Model):
    _inherit = 'delivery.carrier.file'

    @api.model
    def get_type_selection(self):
        result = super(CarrierFile, self).get_type_selection()
        if 'NACEX' not in result:
            result.append(('NACEX', 'Envíos NACEX-API'))
        return result


    type = fields.Selection(get_type_selection, 'Type', required=True)
    nacex_api_debug = fields.Boolean('Nacex api Debug flag', default=False)
    nacex_api_pwd = fields.Char('Nacex api pass')
    nacex_api_user = fields.Char('Nacex api User')
    nacex_api_url = fields.Char('Nacex api URL')
    nacex_api_del_cli = fields.Char('Nacex api del_cli')
    nacex_api_num_cli = fields.Char('Nacex api num_cli')
    nacex_api_tip_ser = fields.Char('Nacex api tip_ser', default='27')
    nacex_api_tip_cob = fields.Char('Nacex api tip_cob', default='O')


CarrierFile()


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    carrier_tracking_url = fields.Char()
    carrier_operation_id = fields.Char()


    @api.multi
    def action_done(self):
        if self.carrier_id:
            if self.carrier_id.name == 'NACEX API':
                api = nacex.API()
                if self.number_of_packages == 1:
                    data = {
                        'del_cli': self.carrier_id.carrier_file_id.nacex_api_del_cli,
                        'num_cli': self.carrier_id.carrier_file_id.nacex_api_num_cli,
                        'fec': datetime.now().strftime('%d/%m/%Y'),
                        'tip_ser': self.carrier_id.carrier_file_id.nacex_api_tip_ser,
                        'tip_cob': self.carrier_id.carrier_file_id.nacex_api_tip_cob,
                        'exc': '0',
                        'ref_cli': self.name,
                        'tip_env': '2',
                        'bul': '1',
                        'kil': '2',
                        'nom_ent': self.partner_id.name,
                        'per_ent': self.partner_id.name,
                        'dir_ent': self.partner_id.street,
                        'pais_ent': self.partner_id.country_id.code,
                        'cp_ent': self.partner_id.zip,
                        'pob_ent': self.partner_id.city,
                        'tel_ent': self.partner_id.phone or self.partner_id.mobile,
                    }

                    if self.sale_id:  
                        if self.sale_id.payment_mode_id.id == 4 :
                            data["tip_cob"] = "O" 
                            data['ree'] = self.sale_id.amount_total
                            data['tip_ree'] = 'O'
                    ok_generated = False
                    res = api.putExpedicion(data=data)
                    if 'data' in res:
                        if 'exp_cod' in res['data']:
                            exp_code = res['data']['exp_cod']
                            tra_code = res['data']['ag_cod/num_exp']
                            self.carrier_tracking_ref = tra_code
                            self.carrier_tracking_url = 'https://www.nacex.es/seguimientoDetalle.do?agencia_origen=%s&numero_albaran=%s&estado=1&internacional=0&externo=N&usr=null&pas=null' % (tra_code.split('/')[0], tra_code.split('/')[1])
                            self.carrier_operation_id = exp_code
                            self._cr.commit()
                            ok_generated = True
                    if not ok_generated:
                        raise exceptions.Warning(("NACEX API ERROR: Creating shipment... %s" % (res)))
                        return
                    
                    data = {
                        'codExp': exp_code,
                        'modelo': 'IMAGEN_b'
                    }

                    ok_label = False
                    tracking = api.getEtiqueta(data=data)
                    if 'data' in tracking:
                        if 'etiqueta' in tracking['data']:
                            ok_label = True
                    if not ok_label:
                        raise exceptions.Warning(("NACEX API ERROR: Generating label... %s" % (res)))
                        return
                    blabel = tracking['data']['etiqueta']
                    png = base64.urlsafe_b64decode(bytes(blabel+"===="))
                    #save attachment
                    attachment = {}
                    attachment['name'] = exp_code
                    attachment['datas_fname'] = attachment['name'] + '.png'
                    attachment['res_model'] = 'stock.picking'
                    attachment['res_id'] = self.id
                    attachment['datas'] = base64.b64encode(png)
                    attachment['file_type'] ='image/png'
                    att = self.env['ir.attachment'].create(attachment)

                    self.carrier_file_generated = True
                    self._cr.commit()

                    buf = io.BytesIO()
                    img = Image.open(io.BytesIO(png)).transpose(Image.ROTATE_270)
                    img.save(buf, format='PNG')
                    pdf_label = buf.getvalue() 
                    f = tempfile.NamedTemporaryFile(delete=False)
                    f.write(pdf_label)
                    f.close()
                    subprocess.call(['lp', '-h', 'localhost:1631', '-d', 'Zebra_Nacex',f.name], shell=False)
                else:
                    raise exceptions.Warning(("NACEX API ERROR: You must set a number of packages = 1"))

        result = super(stock_picking, self).action_done()
        return result

    @api.multi
    def do_transfer(self):
        if self.carrier_id:
            if self.carrier_id.name == 'NACEX API':
                api = nacex.API()
                if self.number_of_packages == 1:
                    data = {
                        'del_cli': self.carrier_id.carrier_file_id.nacex_api_del_cli,
                        'num_cli': self.carrier_id.carrier_file_id.nacex_api_num_cli,
                        'fec': datetime.now().strftime('%d/%m/%Y'),
                        'tip_ser': self.carrier_id.carrier_file_id.nacex_api_tip_ser,
                        'tip_cob': self.carrier_id.carrier_file_id.nacex_api_tip_cob,
                        'exc': '0',
                        'ref_cli': self.name,
                        'tip_env': '2',
                        'bul': '1',
                        'kil': '2',
                        'nom_ent': self.partner_id.name,
                        'per_ent': self.partner_id.name,
                        'dir_ent': self.partner_id.street,
                        'pais_ent': self.partner_id.country_id.code,
                        'cp_ent': self.partner_id.zip,
                        'pob_ent': self.partner_id.city,
                        'tel_ent': self.partner_id.phone or self.partner_id.mobile,
                    }

                    if self.sale_id:  
                        if self.sale_id.payment_mode_id.id == 4 :
                            data["tip_cob"] = "O" 
                            data['ree'] = self.sale_id.amount_total
                            data['tip_ree'] = 'O'
                    ok_generated = False
                    res = api.putExpedicion(data=data)
                    if 'data' in res:
                        if 'exp_cod' in res['data']:
                            exp_code = res['data']['exp_cod']
                            tra_code = res['data']['ag_cod/num_exp']
                            self.carrier_tracking_ref = tra_code
                            self.carrier_tracking_url = 'https://www.nacex.es/seguimientoDetalle.do?agencia_origen=%s&numero_albaran=%s&estado=1&internacional=0&externo=N&usr=null&pas=null' % (tra_code.split('/')[0], tra_code.split('/')[1])
                            self.carrier_operation_id = exp_code
                            self._cr.commit()
                            ok_generated = True
                    if not ok_generated:
                        raise exceptions.Warning(("NACEX API ERROR: Creating shipment... %s" % (res)))
                        return
                    
                    data = {
                        'codExp': exp_code,
                        'modelo': 'IMAGEN_b'
                    }

                    ok_label = False
                    tracking = api.getEtiqueta(data=data)
                    if 'data' in tracking:
                        if 'etiqueta' in tracking['data']:
                            ok_label = True
                    if not ok_label:
                        raise exceptions.Warning(("NACEX API ERROR: Generating label... %s" % (res)))
                        return
                    blabel = tracking['data']['etiqueta']
                    png = base64.urlsafe_b64decode(bytes(blabel+"===="))
                    #save attachment
                    attachment = {}
                    attachment['name'] = exp_code
                    attachment['datas_fname'] = attachment['name'] + '.png'
                    attachment['res_model'] = 'stock.picking'
                    attachment['res_id'] = self.id
                    attachment['datas'] = base64.b64encode(png)
                    attachment['file_type'] ='image/png'
                    att = self.env['ir.attachment'].create(attachment)

                    self.carrier_file_generated = True
                    self._cr.commit()

                    buf = io.BytesIO()
                    img = Image.open(io.BytesIO(png)).transpose(Image.ROTATE_270)
                    img.save(buf, format='PNG')
                    pdf_label = buf.getvalue() 
                    f = tempfile.NamedTemporaryFile(delete=False)
                    f.write(pdf_label)
                    f.close()
                    subprocess.call(['lp', '-h', 'localhost:1631', '-d', 'Zebra_Nacex',f.name], shell=False)

                else:
                    raise exceptions.Warning(("NACEX API ERROR: You must set a number of packages = 1"))
        result = super(stock_picking, self).do_transfer()
        return result

    @api.multi
    def cancel_nacex_api(self):
        if self.carrier_operation_id:
            if self.carrier_id.name == 'NACEX API':
                api = nacex.API()
                res = api.cancelExpedicion(data={'expe_codigo': self.carrier_operation_id})
                if 'status' in res:
                    if res['status'] == 'OK':
                        self.carrier_operation_id = ''
                        self.carrier_file_generated = False
                        self.carrier_tracking_ref = ''
                        self.carrier_tracking_url = ''
                        return
                raise exceptions.Warning(("NACEX API ERROR: error cancelling shipment"))

        
        raise exceptions.Warning(("NACEX API ERROR: You must have a valid carrier_operation_id for nacex"))


    @api.multi
    def regenerate_nacex_api(self):
        if self.carrier_id:
            if self.carrier_id.name == 'NACEX API':
                if self.carrier_operation_id or self.carrier_file_generated or self.carrier_tracking_ref or self.carrier_tracking_url:
                    raise exceptions.Warning(("NACEX API ERROR: Please, cancel prevous shipment"))
                api = nacex.API()
                if self.number_of_packages == 1:
                    data = {
                        'del_cli': self.carrier_id.carrier_file_id.nacex_api_del_cli,
                        'num_cli': self.carrier_id.carrier_file_id.nacex_api_num_cli,
                        'fec': datetime.now().strftime('%d/%m/%Y'),
                        'tip_ser': self.carrier_id.carrier_file_id.nacex_api_tip_ser,
                        'tip_cob': self.carrier_id.carrier_file_id.nacex_api_tip_cob,
                        'exc': '0',
                        'ref_cli': self.name,
                        'tip_env': '2',
                        'bul': '1',
                        'kil': '2',
                        'nom_ent': self.partner_id.name,
                        'per_ent': self.partner_id.name,
                        'dir_ent': self.partner_id.street,
                        'pais_ent': self.partner_id.country_id.code,
                        'cp_ent': self.partner_id.zip,
                        'pob_ent': self.partner_id.city,
                        'tel_ent': self.partner_id.phone or self.partner_id.mobile,
                    }

                    if self.sale_id:  
                        if self.sale_id.payment_mode_id.id == 4 :
                            data["tip_cob"] = "O" 
                            data['ree'] = self.sale_id.amount_total
                            data['tip_ree'] = 'O'
                    ok_generated = False
                    res = api.putExpedicion(data=data)
                    if 'data' in res:
                        if 'exp_cod' in res['data']:
                            exp_code = res['data']['exp_cod']
                            tra_code = res['data']['ag_cod/num_exp']
                            self.carrier_tracking_ref = tra_code
                            self.carrier_tracking_url = 'https://www.nacex.es/seguimientoDetalle.do?agencia_origen=%s&numero_albaran=%s&estado=1&internacional=0&externo=N&usr=null&pas=null' % (tra_code.split('/')[0], tra_code.split('/')[1])
                            self.carrier_operation_id = exp_code
                            self._cr.commit()
                            ok_generated = True
                    if not ok_generated:
                        raise exceptions.Warning(("NACEX API ERROR: Creating shipment... %s" % (res)))
                        return
                    
                    data = {
                        'codExp': exp_code,
                        'modelo': 'IMAGEN_b'
                    }

                    ok_label = False
                    tracking = api.getEtiqueta(data=data)
                    if 'data' in tracking:
                        if 'etiqueta' in tracking['data']:
                            ok_label = True
                    if not ok_label:
                        raise exceptions.Warning(("NACEX API ERROR: Generating label... %s" % (res)))
                        return
                    blabel = tracking['data']['etiqueta']
                    png = base64.urlsafe_b64decode(bytes(blabel+"===="))
                    #save attachment
                    attachment = {}
                    attachment['name'] = exp_code
                    attachment['datas_fname'] = attachment['name'] + '.png'
                    attachment['res_model'] = 'stock.picking'
                    attachment['res_id'] = self.id
                    attachment['datas'] = base64.b64encode(png)
                    attachment['file_type'] ='image/png'
                    att = self.env['ir.attachment'].create(attachment)

                    self.carrier_file_generated = True
                    self._cr.commit()

                    buf = io.BytesIO()
                    img = Image.open(io.BytesIO(png)).transpose(Image.ROTATE_270)
                    img.save(buf, format='PNG')
                    pdf_label = buf.getvalue() 
                    f = tempfile.NamedTemporaryFile(delete=False)
                    f.write(pdf_label)
                    f.close()
                    subprocess.call(['lp', '-h', 'localhost:1631', '-d', 'Zebra_Nacex',f.name], shell=False)

                else:
                    raise exceptions.Warning(("NACEX API ERROR: You must set a number of packages = 1"))
