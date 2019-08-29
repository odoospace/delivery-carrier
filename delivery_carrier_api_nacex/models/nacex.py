#!/usr/bin/env python2
import config
import time
import collections
import requests
import urllib
requests.packages.urllib3.disable_warnings()

import logging

_logger = logging.getLogger(__name__)

METHODS = {
    'getCodigosReferencia':{
        'in': ['ref'],
        'out': ['Fecha_recogida', 'reco_codigo', 'Fecha_expedicion', 'expe_codigo']
    },
    'getExpedicion':{
        'in': ['codExp'],
        'out': ['exp_cod', 'ag_cod', 'exp_num', 'cli_ag_cod', 'cli_cod', 'exp_fecha',
         'exp_serv', 'exp_serv_desc', 'exp_env', 'exp_env', 'exp_env_desc', 'exp_bult', 
         'exp_peso', 'exp_exc', 'exp_multiref', 'ent_nom', 'ent_dir', 'ent_cp', 'ent_pob', 
         'ent_prov', 'ent_contacto', 'ent_tlf', 'ent_obs']
    },
    'getExpedicion2':{
        'in': ['del' 'num'],
        'out': ['exp_cod', 'ag_cod', 'exp_num', 'cli_ag_cod', 'cli_cod', 'exp_fecha',
         'exp_serv', 'exp_serv_desc', 'exp_env', 'exp_env', 'exp_env_desc', 'exp_bult', 
         'exp_peso', 'exp_exc', 'exp_multiref', 'ent_nom', 'ent_dir', 'ent_cp', 'ent_pob', 
         'ent_prov', 'ent_contacto', 'ent_tlf', 'ent_obs']
    },
    'getAgencia': {
        'in': ['*cp'],
        'out': ['cod_age', 'nom_age', 'dir_age', 'tel_age'],
    },
    'putExpedicion': {
        'in': [
            '*del_cli', '*num_cli', 'dep_cli', 'fec', '*tip_ser', '*tip_cob',
            'exc', 'ref_cli', '*tip_env', '*bul', '*kil', 'nom_rec', 'dir_rec', 'cp_rec',
            'pob_rec', 'tel_rec', '*nom_ent', 'per_ent', '*dir_ent',
            '*pais_ent', '*cp_ent', '*pob_ent', '*tel_ent', 'ree', 'tip_ree',
            'obs1', 'obs2', 'obs3', 'obs4', 'ret', 'ges', 'ok15', 'pre',
            'tip_seg', 'seg', 'tip_ea', 'ealerta', 'alto', 'ancho', 'largo',
            'con', 'val_dec', 'dig', 'num_dig', 'ins_adi1', 'ins_adi2',
            'ins_adi3', 'ins_adi4', 'ins_adi5', 'ins_adi6', 'ins_adi7',
            'ins_adi8', 'ins_adi9', 'ins_adi10', 'ins_adi11', 'ins_adi12',
            'ins_adi13', 'ins_adi14', 'ins_adi15', 'tip_pre1', 'mod_pre1', 
            're1', 'msg1', 'tip_pre2', 'mod_pre2', 'pre2', 'msg2', 'tip_pre3',
            'mod_pre3', 'pre3', 'msg3', 'tip_pre4', 'mod_pre4', 'pre4',
            'msg4', 'tip_pre5', 'mod_pre5', 'pre5', 'msg5', 'ins_adi', 'cam_serv',
            'shop_codigo', 'frec_codigo'
        ],
        'out': [
            'exp_cod', 'ag_cod/num_exp', 'color', 'ent_ruta', 'ent_cod',
            'ent_nom', 'ent_tlf', 'serv', 'hora_entrega', 'barcode',
            'fecha_objetivo', 'cambios'
        ]
    },
    'cancelExpedicion': {
        'in': ['expe_codigo', 'origen', 'albaran', 'ref'],
        'out': ['mensaje'],
    },
    'getEtiqueta': {
        'in': ['codExp', 'modelo'],
        'out': ['etiqueta'],
    },
    # campos: fecha_alta, referencia, tracking, remitente, direccion_origen,
    # cp_origen, ciudad_origen, agencia_entrega, consignatario, direccion_entrega,
    # cp_entrega, ciudad_entrega, telefono_entrega, departamento_cliente, bultos,
    # kilos, importe_reembolso, observaciones_datos, tipo_reembolso,
    # servicio agencia_estado fecha_estado
    'getListadoExpediciones': {
        'in': ['*fecha_ini', '*fecha_fin', 'campos'],
        'out': [],
    }
}

class FieldError(Exception):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)


class API():
    def __init__(self, content_type='text/html;charset=UTF-8'):
        c = config.NACEX
        self.user = c.user
        self.pwd = c.pwd # pass is reserved
        self.url = c.url
        self.debug = c.debug

        # add methods in a dynamic way
        for method in METHODS.keys():
            setattr(self, method, lambda data, method=method: self._send.__call__(method, data))

    def _send(self, method, data):
        """data is a dictionary"""
        # if self.debug:
        #     print 'CALL %s with %s' % (method, data)
        # prepare DATA
        newdata = collections.OrderedDict()
        for _field in METHODS[method]['in']:
            if _field[0] == '*':
                field = _field[1:]
            else:
                field = _field
            if field in data:
                newdata[field] = data[field]
            elif _field[0] == '*':
                raise FieldError('ERROR! Mandatory field empty: %s' % field)

        # prepare URL
        if not method or not method in METHODS:
            return

        url = self.url
        url += 'method=%s' % method
        url += '&user=%s' % self.user
        url += '&pass=%s' % self.pwd
        
        if data:
            url += '&data='
        
        url_data = ''
        for k, v in newdata.items():
            if v:
                url_data += '%s=%s' % (k, urllib.quote_plus(v)) + '|'
        url_data = url_data[:-1]

        url += url_data

        # if self.debug:
        #     print 'URL:', url
        _logger.info('NNN NACEX API requesting url: %s' % url)
        # do request
        res = requests.get(url)
        # if self.debug:
        #     print 'RESPONSE:', res, res.text

        if 'ERROR' in res.text:
            return {
                'status': 'ERROR',
                'message': res.text

            }

        res_fields = res.text.split('|')

        # parse response
        res_obj = {
            'status': 'OK',
            'data': {}
        }
        if not METHODS[method]['out']:
            res_obj['data'] = []
            for d in res_fields:
                res_obj['data'].append(d.split('~'))
        else:
            for i, field in enumerate(METHODS[method]['out']):
                res_obj['data'][field] = res_fields[i]
                
        return res_obj


if __name__ == '__main__':
    api = API()

    """
    data = {
        'fecha_ini': '24/01/2019',
        'fecha_fin': '25/01/2019',
        'campos': 'fecha_alta;referencia;tracking;direccion_entrega'
    }
    print api.getListadoExpediciones(data=data)
    """

    """
    data = {
        'expe_codigo': '237313460'
    }
    print api.cancelExpedicion(data=data)
    print
    stop
    """
    

    """
    data = {
        'cp': '17005'
    }
    print api.getAgencia(data=data)
    print
    """
    
    data = {
        'del_cli': '1711',
        'num_cli': '03297',
        'fec': '30/07/2019',
        'tip_ser': '27',
        'tip_cob': 'O',
        'exc': '0',
        'ref_cli': 'INFORMATICA',
        'tip_env': '2',
        'bul': '1',
        'kil': '2',
        'nom_ent': 'PRUEBA - NO USAR',
        'per_ent': 'PRUEBA - NO USAR',
        'dir_ent': 'PRUEBA - NO USAR',
        'pais_ent': 'ES',
        'cp_ent': '46017',
        'pob_ent': 'VALENCIA',
        'tel_ent': '159487263',
    }
    res = api.putExpedicion(data=data)
    # print res
    exp_code = res['data']['exp_cod']

    data = {
        'codExp': exp_code,
        'modelo': 'IMAGEN'
    }
    # print api.getEtiqueta(data=data)
    # print

    data = {
        'expe_codigo': exp_code
    }
    # print api.cancelExpedicion(data=data)
    # print

    