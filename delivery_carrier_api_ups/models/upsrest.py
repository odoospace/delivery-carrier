# -*- coding: utf-8 -*-
import requests
import json
from base64 import b64decode

class UPSAPI():
    def __init__(self, username, password, license, context='test'):
        """everything starts here..."""
        self.username = username
        self.password = password
        self.license = license
        self.headers = {'Accept': 'text/plain', 'Content-type': 'application/json'}
        if context == 'test':
            self.url = 'https://wwwcie.ups.com/rest'
        else:
            # stop
            self.url = 'https://onlinetools.ups.com/rest'

    def ship(self):
        payload = {
            "Security": self._security(),
            "ShipmentRequest": self._ship()
        }
        res = requests.post(self.url+'/Ship', data=json.dumps(payload), headers=self.headers)
        print res.json()

    def ship_with_data(self, data):
        payload = {
            "Security": self._security(),
            "ShipmentRequest": data
        }
        res = requests.post(self.url+'/Ship', data=json.dumps(payload), headers=self.headers)
        return res.json()

    def label(self):
        payload = {
            "Security": self._security(),
            "LabelRecoveryRequest": self._label()
        }
        res = requests.post(self.url+'/LBRecovery', data=json.dumps(payload), headers=self.headers)
        #print res.json().keys()
        data = res.json()
        pdfdata = data['LabelRecoveryResponse']['LabelResults']['Receipt']['Image']['GraphicImage']
        open('ups.pdf', 'w').write(b64decode(pdfdata))

    def label_with_data(self, label):
        payload = {
            "Security": self._security(),
            "LabelRecoveryRequest": label
        }
        res = requests.post(self.url+'/LBRecovery', data=json.dumps(payload), headers=self.headers)
        return res.json()
        # data = res.json()
        # pdfdata = data['LabelRecoveryResponse']['LabelResults']['LabelImage']['GraphicImage']
        # open('ups.pdf', 'w').write(b64decode(pdfdata))
        # return data

    def _security(self):
        # "Security": {
        return  {                                                            
            "UsernameToken": {
                "Username": self.username,
                "Password": self.password 
            },
            "UPSServiceAccessToken": {
                "AccessLicenseNumber": self.license
            }
        }

    def _track(self):
        return {
            "TrackRequest": {
                "Request": {
                    "RequestAction": "Track",
                    "RequestOption": "activity"
                },
                "InquiryNumber": "XXX"
            }
        }
    
    def _label(self):
        # "LabelRecoveryRequest": {
        return {
            "LabelSpecification": {
                "LabelImageFormat": {
                    "Code": "GIF"
                },
                "HTTPUserAgent": "Mozilla/4.5"
            },
            "Translate": {
                "LanguageCode": "eng",
                "DialectCode": "GB",
                "Code": "01"
            },
            "TrackingNumber": "XXX"
        }
    
    def _ship(self):
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
                    "Name": "XXX",
                    "TaxIdentificationNumber": "ESB12345678", 
                    "Phone": {
                        "Number": "+12345678901",
                    },
                    "ShipperNumber": self.username,
                    "Address": {
                        "AddressLine": "STREET",
                        "City": "CITY",
                        "PostalCode": "ZIP",
                        "CountryCode": "COUNTRYCODE"
                    }
                },
                "ShipTo": {
                    "Name": "CLIENT NAME",
                    "Phone": {
                        "Number": "CLIENTPHONE"
                    }, 
                    "Address": {
                        "AddressLine": "STREET",
                        "City": "CITY",
                        "PostalCode": "ZIP",
                        "CountryCode": "COUNTRYCODE"
                    }
                },
                "ShipFrom": {
                    "Name": "SHIPPER",
                    "Phone": {
                        "Number": "+NUMBER"
                    },
                    "Address": {
                        "AddressLine": "STREET",
                        "City": "CITY",
                        "PostalCode": "ZIP",
                        "CountryCode": "COUNTRYCODE"
                    }
                },
                "PaymentInformation": {
                    "ShipmentCharge": {
                        "Type": "01",
                        "BillShipper": {
                            "AccountNumber": self.username
                        }
                    }
                },
                "Service": {
                    "Code": "65",
                    "Description": "UPS Saver"
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
