#!/usr/bin/env python
# coding=utf-8
from datetime import datetime


def convert_identifier(key, val, es, nss, tmpl):
    return "http://hdl.handle.net/" + val.replace("hdl:", "")

def convert_availability(key, val, es, nss, tmpl):
    if val == "available-restrictedUse":
        return "RES"

def convert_name(xpath_key, val, es, nss, tmpl):
    authors = []
    for el in es:
        sn = el.find(u"./xmlns:surname", namespaces=nss).text
        fn = el.find(u"./xmlns:givenName", namespaces=nss).text
        authors.append(u"%s %s" % (fn, sn))
    tmpl.fill_many(xpath_key, authors)


settings = {
    "handle": "./xmlns:identificationInfo/xmlns:identifier",

    "dublin_core.xml": {
        "map": {
            "./xmlns:identificationInfo/xmlns:resourceName": ".//dcvalue[@element='title']",
            "./xmlns:identificationInfo/xmlns:identifier": (".//dcvalue[@element='identifier']", convert_identifier),
            "./xmlns:distributionInfo/xmlns:availability": (".//dcvalue[@element='rights'][@qualifier='label']", convert_availability),
            "./xmlns:distributionInfo/xmlns:iprHolder/": (".//dcvalue[@element='contributor'][@qualifier='author']", convert_name),
        },
        "hardcode": {
            ".//dcvalue[@element='description'][@qualifier='provenance']": u"Transformed to XXX at [%s] by [automatic script]" % datetime.now()
        }
    },
    "metadata_local.xml": {
        "map": {
        },
        "hardcode":{

        }
    }

}
