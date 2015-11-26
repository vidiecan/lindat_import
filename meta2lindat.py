#!/usr/bin/env python
# coding=utf-8
"""
Creating DSpace imports
python2.7 meta2lindat.py input/*

Import done by
./dspace import --add --eperson=EPERSON@EMAIL --collection=16 --source=/home/jmisutka/lrt --mapfile ./mapfile

"""
import xml.etree.ElementTree
import glob
import os
import sys
import logging

from utils import templated_xml

_logger = None

settings = {
    "output": "output",
}

#
#

if sys.version_info < (2, 7) or sys.version_info >= (3, 0):
    print "Sorry, not supported python version, get yourself python v2.7"
    sys.exit(1)


# noinspection PyMethodMayBeStatic
class dspace_ingestion(object):
    """
        If there are more field types converted to one subject
        they all should be arrays or the template value will be overwritten.
    """

    def __init__(self, output_dir):
        self._out_dir = output_dir

    def write_xml(self, output_dir, name, contents):
        out_filename = os.path.join(output_dir, name)
        if os.path.exists(out_filename):
            os.remove(out_filename)
        with open(out_filename, mode="w+") as fout:
            fout.write(contents)

    def write(self, handle, pos, name_contents_arr):
        """
            Create dir structure as specified in
            https://wiki.duraspace.org/display/DSDOC4x/Importing+and+Exporting+Items+via+Simple+Archive+Format#ImportingandExportingItemsviaSimpleArchiveFormat-ExportingItems
        """
        # create main dir
        directory_str = os.path.join(self._out_dir, "item_%03d" % pos)
        if not os.path.exists(directory_str):
            os.makedirs(directory_str)

        # create empty contents file
        contents_filestr = os.path.join(directory_str, "contents")
        if os.path.exists(contents_filestr):
            os.remove(contents_filestr)
        open(contents_filestr, "w+").close()
        
        # create handle
        handle_filestr = os.path.join(directory_str, "handle")
        with open(handle_filestr, "w+") as fout:
            fout.write(handle)

        if name_contents_arr is not None:
            for name, xml_content in name_contents_arr:
                self.write_xml(directory_str, name, xml_content)


class meta(object):

    nss = {'xmlns': 'http://www.ilsp.gr/META-XMLSchema'}

    def __init__(self, root, tmpl, mapping):
        self._root = root
        self._tmpl = tmpl
        self._mapping = mapping

    @staticmethod
    def from_file(file_str, name, mapping):
        if not os.path.exists(file_str):
            _logger.info(u"NOT Processing [%s] because it does not exist!", file_str)
            sys.exit(1)
        tmpl_file_str = name + ".template"
        if not os.path.exists(tmpl_file_str):
            _logger.info(u"NOT Processing [%s] because template [%s] does not exist!", file_str, tmpl_file_str)
            sys.exit(1)

        _logger.info(u"Processing [%s] to [%s]", file_str, name)
        xml_root = xml.etree.ElementTree.parse(file_str).getroot()
        tmpl = templated_xml(tmpl_file_str)
        return meta(xml_root, tmpl, mapping)

    @staticmethod
    def handle(file_str, xpath):
        xml_root = xml.etree.ElementTree.parse(file_str).getroot()
        return xml_root.findall(xpath, namespaces=meta.nss)[0].text.replace("hdl:", "")

    def format(self):
        # hardcode if any
        for k, v in self._mapping["hardcode"].iteritems():
            self._tmpl.fill(k, v.strip())

        # dynamic
        for xpath_input, xpath_template in self._mapping["map"].iteritems():
            input_value = self._root.findall(xpath_input, namespaces=meta.nss)
            if input_value is None:
                _logger.warn("[%s] is empty", xpath_input)
                continue
            if 1 < len(input_value):
                _logger.warn("[%s] has more values", xpath_input)
                continue
            value = input_value[0].text.strip()
            if isinstance(xpath_template, basestring):
                self._tmpl.fill(xpath_template, value)
            elif isinstance(xpath_template, (tuple, list)):
                xpath_template_str, callable = xpath_template
		res = callable(xpath_template_str, value, input_value, meta.nss, self._tmpl)
		if res is not None:
                    self._tmpl.fill(xpath_template_str, res)

        return self._tmpl.utf8_xml_string()


#
#

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG, format='%(asctime)-15s %(message)s')
    _logger = logging.getLogger()

    dspace = dspace_ingestion(settings["output"])

    file_in_glob = sys.argv[1]
    from metamap import settings as metamaps
    for pos, f in enumerate(glob.glob(file_in_glob)):
        name_content_arr = []
        handle = meta.handle(f, metamaps["handle"])
        for k, v in metamaps.iteritems():
            if not k.endswith("xml"):
                continue
            m = meta.from_file(f, k, v)
            contents = m.format()
            name_content_arr.append( (k, contents) )
        dspace.write(handle, pos, name_content_arr)
