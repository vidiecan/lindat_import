#!/usr/bin/env python
# coding=utf-8
"""
    utils
"""
import copy
import xml.etree.ElementTree as ElementTree


# noinspection PyDeprecation
class templated_xml(object):

    def __init__(self, template_filename):
        template = open(template_filename).read()
        self.xml = ElementTree.ElementTree(ElementTree.fromstring(template))
        self.parenthack = dict((c, p) for p in self.xml.getiterator() for c in p)
        self._done = set()

    def fill(self, xpath_str, value):
        self.fill_many(xpath_str, [value])

    def fill_many(self, xpath_str, value_arr):
        try:
            if len(value_arr) == 0:
                return
            # set the default one
            element = self.xml.find(xpath_str)
            start_index = 0
            if element.text is None or len(element.text) == 0:
                assert xpath_str not in self._done
                element.text = value_arr[0]
                start_index += 1
            # indicate we have done it for this field - error checking
            self._done.add(xpath_str)

            parent = self.parenthack[element]
            position = parent.getchildren().index(element)

            for value in value_arr[start_index:]:
                position += 1
                new_el = ElementTree.Element(element.tag)
                new_el.attrib = copy.copy(element.attrib)
                new_el.text = value.strip()
                parent.insert(position, new_el)
        except:
            raise

    def utf8_xml_string(self):
        todel = []
        for e in self.xml.getroot().getchildren():
            if e.text is None or len(e.text.strip()) == 0:
                todel.append(e)
        for e in todel:
            self.xml.getroot().remove(e)
        xml_s = ElementTree.tostring(self.xml.getroot(), encoding="utf-8")

        # ehm
        try:
            import xml.dom.minidom
            xml_parsed = xml.dom.minidom.parseString(xml_s)
            xml_s = xml_parsed.toprettyxml()
        except:
            pass
        return xml_s

