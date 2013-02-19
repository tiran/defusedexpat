# defusedexpat
#
# Copyright (c) 2013 by Christian Heimes <christian@python.org>
# Licensed to PSF under a Contributor Agreement.
# See http://www.python.org/psf/license for licensing details.

from __future__ import print_function
import os
import sys
import unittest
import re
import io

import defusedexpat
import pyexpat
import _elementtree

# after defusedexpat
from xml.parsers import expat
from xml.parsers.expat import errors
from xml.etree import cElementTree as ET
from xml.sax.saxutils import XMLGenerator
from xml import sax
from xml.dom import pulldom
from xml.dom import minidom

HERE = os.path.dirname(os.path.abspath(__file__))
PY3 = sys.version_info[0] > 2
PY26 = sys.version_info[:2] == (2, 6)
PY31 = sys.version_info[:2] == (3, 1)

if PY26 or PY31:
    ParseError = SyntaxError
else:
    ParseError = ET.ParseError

# prevent web access
# based on Debian's rules, Port 9 is discard
os.environ["http_proxy"] = "http://127.0.9.1:9"
os.environ["https_proxy"] = os.environ["http_proxy"]
os.environ["ftp_proxy"] = os.environ["http_proxy"]

quadratic_bomb = b"""\
<!DOCTYPE bomb [
<!ENTITY a "MARK" >
<!ENTITY b "&a;&a;" >
<!ENTITY c "&b;&b;" >
]>
<bomb>&a;</bomb>
"""


if PY26 or PY31:
    class _AssertRaisesContext(object):
        def __init__(self, expected, test_case, expected_regexp=None):
            self.expected = expected
            self.failureException = test_case.failureException
            self.expected_regexp = expected_regexp

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, tb):
            if exc_type is None:
                try:
                    exc_name = self.expected.__name__
                except AttributeError:
                    exc_name = str(self.expected)
                raise self.failureException(
                    "{0} not raised".format(exc_name))
            if not issubclass(exc_type, self.expected):
                # let unexpected exceptions pass through
                return False
            self.exception = exc_value # store for later retrieval
            if self.expected_regexp is None:
                return True

            expected_regexp = self.expected_regexp
            if isinstance(expected_regexp, basestring):
                expected_regexp = re.compile(expected_regexp)
            if not expected_regexp.search(str(exc_value)):
                raise self.failureException('"%s" does not match "%s"' %
                         (expected_regexp.pattern, str(exc_value)))
            return True


class DefusedExpatTests(unittest.TestCase):
    dtd_external_ref = False

    xml_dtd = os.path.join(HERE, "xmltestdata", "dtd.xml")
    xml_external = os.path.join(HERE, "xmltestdata", "external.xml")
    xml_quadratic = os.path.join(HERE, "xmltestdata", "quadratic.xml")
    xml_bomb = os.path.join(HERE, "xmltestdata", "xmlbomb.xml")

    if PY26 or PY31:
        # old Python versions don't have these useful test methods
        def assertRaises(self, excClass, callableObj=None, *args, **kwargs):
            context = _AssertRaisesContext(excClass, self)
            if callableObj is None:
                return context
            with context:
                callableObj(*args, **kwargs)

        def assertIn(self, member, container, msg=None):
            if member not in container:
                standardMsg = '%s not found in %s' % (repr(member),
                                                      repr(container))
                self.fail(self._formatMessage(msg, standardMsg))

    def setUp(self):
        pyexpat.set_reset_dtd(False)
        pyexpat.set_max_entity_expansions(
            pyexpat.XML_DEFAULT_MAX_ENTITY_EXPANSIONS)
        pyexpat.set_max_entity_indirections(
            pyexpat.XML_DEFAULT_MAX_ENTITY_INDIRECTIONS)

    def test_xmlbomb_protection_available(self):
        self.assertTrue(pyexpat.XML_BOMB_PROTECTION)

    def test_defaults(self):
        self.assertEqual(pyexpat.get_reset_dtd(), False)
        self.assertEqual(pyexpat.get_max_entity_expansions(),
                         pyexpat.XML_DEFAULT_MAX_ENTITY_EXPANSIONS)
        self.assertEqual(pyexpat.get_max_entity_indirections(),
                         pyexpat.XML_DEFAULT_MAX_ENTITY_INDIRECTIONS)

        pyexpat.set_reset_dtd(True)
        pyexpat.set_max_entity_expansions(10)
        pyexpat.set_max_entity_indirections(10)

        self.assertEqual(pyexpat.get_reset_dtd(), True)
        self.assertEqual(pyexpat.get_max_entity_expansions(), 10)
        self.assertEqual(pyexpat.get_max_entity_indirections(), 10)

        p = pyexpat.ParserCreate()
        self.assertEqual(p.max_entity_indirections, 10)
        self.assertEqual(p.max_entity_expansions, 10)
        self.assertEqual(p.reset_dtd, True)

    def test_xmlbomb_exponential(self):
        # test that the maximum indirection limitation prevents exponential
        # entity expansion attacks (billion laughs). Every expansion increases
        # the indirection level. The result of an expansion is never cached.
        p = expat.ParserCreate()
        self.assertEqual(p.max_entity_indirections, 40)
        with self.assertRaises(expat.ExpatError) as e:
            with open(self.xml_bomb, "rb") as f:
                p.ParseFile(f)
        self.assertEqual(str(e.exception),
                         "entity indirection limit exceeded: "
                         "line 7, column 6")

        p = expat.ParserCreate()
        p.max_entity_indirections = 0
        with open(self.xml_bomb, "rb") as f:
            p.ParseFile(f)

        p = expat.ParserCreate()
        p.max_entity_indirections = 72 # 8 * 8 + 8
        with open(self.xml_bomb, "rb") as f:
            p.ParseFile(f)

    def test_xmlbomb_quadratic(self):
        # test that the total amount of expanded entities chars is limited to
        # prevent quadratic blowout attacks.
        p = expat.ParserCreate()
        self.assertEqual(p.max_entity_expansions, 8 * 1024 ** 2)

        # lower limit to 1024, must fail with one entity of 1025 chars
        p.max_entity_expansions = 1024
        xml = quadratic_bomb.replace(b"MARK", b"a" * 1025)
        with self.assertRaises(expat.ExpatError) as e:
            p.Parse(xml)
        self.assertEqual(str(e.exception),
                         "document's entity expansion limit exceeded: "
                         "line 6, column 6")

        # but passes with an entity of 1024 chars
        xml = quadratic_bomb.replace(b"MARK", b"a" * 1024)
        p = expat.ParserCreate()
        p.max_entity_expansions = 1024
        p.Parse(xml)

        # one level of indirection, a = "&b;&b;" adds 6 chars
        xml = quadratic_bomb.replace(b"MARK", b"a" * 512)
        xml = xml.replace(b"<bomb>&a;</bomb>", b"<bomb>&b;</bomb>")
        p = expat.ParserCreate()
        p.max_entity_expansions = 1024
        with self.assertRaises(expat.ExpatError) as e:
            p.Parse(xml)
        self.assertEqual(str(e.exception),
                         "document's entity expansion limit exceeded: "
                         "line 6, column 6")

        p = expat.ParserCreate()
        p.max_entity_expansions = 1030 # 2 * x512 + 6
        p.Parse(xml)

        # test default limit of 8 MB
        xml = quadratic_bomb.replace(b"MARK", b"a" * 2 * 1024 ** 2)
        xml = xml.replace(b"<bomb>&a;</bomb>", b"<bomb>&c;</bomb>")
        p = expat.ParserCreate()
        with self.assertRaises(expat.ExpatError) as e:
            p.Parse(xml)
        self.assertEqual(str(e.exception),
                         "document's entity expansion limit exceeded: "
                         "line 6, column 6")

        # disabled limit
        p = expat.ParserCreate()
        p.max_entity_expansions = 0
        p.Parse(xml)

    def test_xmlbomb_resetdtd(self):
        # with reset_dtd all DTD information are ignored
        p = expat.ParserCreate()
        self.assertEqual(p.reset_dtd, False)
        p.reset_dtd = True
        with self.assertRaises(expat.ExpatError) as e:
            with open(self.xml_bomb, "rb") as f:
                p.ParseFile(f)
        self.assertEqual(str(e.exception), "undefined entity: line 7, column 6")

    def test_xmlbomb_cetree(self):
        # ElementTree does NOT retrieve DTD
        ET.parse(self.xml_dtd)

        # and raises an exception because it doesn't expand external entities
        with self.assertRaises(ParseError) as e:
            ET.parse(self.xml_external)
        if PY31:
            # Python 3.1 bug
            self.assertTrue(str(e.exception).startswith("undefined entity"),
                            str(e.exception))
        else:
            self.assertEqual(str(e.exception),
                "undefined entity &ee;: line 4, column 6")

        with self.assertRaises(ParseError) as e:
            ET.parse(self.xml_bomb)
        self.assertEqual(str(e.exception),
                         "entity indirection limit exceeded: line 7, column 6")

        eight_mb = 1024 ** 2 * 8
        with self.assertRaises(ParseError) as e:
            xml = quadratic_bomb.replace(b"MARK", b"a" * (eight_mb + 1))
            ET.fromstring(xml)

    def parse_sax(self, xmlfile, **kwargs):
        if PY3:
            result = io.StringIO()
        else:
            result = io.BytesIO()
        handler = XMLGenerator(result)
        sax.parse(xmlfile, handler, **kwargs)
        return result.getvalue()

    def test_sax_external_entity(self):
        try:
            defusedexpat.unmonkey_patch()
            # IOError caused by proxy settings, works only on POSIX
            if os.name == "posix":
                self.assertRaises(IOError, self.parse_sax, self.xml_external)
        finally:
            defusedexpat.monkey_patch()
        value = self.parse_sax(self.xml_external)
        self.assertIn("<root></root>", value)

    def test_pulldom_externals(self):
        try:
            defusedexpat.unmonkey_patch()
            # pulldom does DTD retrieval
            dom = pulldom.parse(self.xml_dtd)
            if os.name == "posix":
                self.assertRaises(IOError, list, dom)
            # and loads external entities by default
            dom = pulldom.parse(self.xml_external)
            if os.name == "posix":
                self.assertRaises(IOError, list, dom)
        finally:
            defusedexpat.monkey_patch()

        events = list(pulldom.parse(self.xml_dtd))
        self.assertEqual(events[9][0], 'CHARACTERS')
        self.assertEqual(events[9][1].data, "text")

        events = list(pulldom.parse(self.xml_external))
        self.assertEqual([e[0] for e in events],
                         ['START_DOCUMENT', 'START_ELEMENT', 'END_ELEMENT'])

    def test_minidom_externals(self):
        try:
            defusedexpat.unmonkey_patch()
            # minidom does NOT retrieve DTDs
            dom = minidom.parse(self.xml_dtd)
            # and does NOT load  external entities by default
            minidom.parse(self.xml_external)
        finally:
            defusedexpat.monkey_patch()


def test_main():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(DefusedExpatTests))
    return suite

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(test_main())
    sys.exit(not result.wasSuccessful())
