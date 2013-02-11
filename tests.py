from __future__ import print_function
import os
import sys
import unittest

import defusedexpat
import pyexpat
import _elementtree

# after defuxedexpat
from xml.parsers import expat
from xml.parsers.expat import errors
from xml.etree import cElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

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

class DefusedExpatTests(unittest.TestCase):
    dtd_external_ref = False

    xml_dtd = os.path.join(HERE, "xmltestdata", "dtd.xml")
    xml_external = os.path.join(HERE, "xmltestdata", "external.xml")
    xml_quadratic = os.path.join(HERE, "xmltestdata", "quadratic.xml")
    xml_bomb = os.path.join(HERE, "xmltestdata", "xmlbomb.xml")

    def test_xmlbomb_protection_available(self):
        self.assertTrue(pyexpat.XML_BOMB_PROTECTION)

    def test_xmlbomb_exponential(self):
        # test that the maximum indirection limitation prevents exponential
        # entity expansion attacks (billion laughs). Every expansion increases
        # the indirection level. The result of an expansion is never cached.
        p = expat.ParserCreate()
        self.assertEqual(p.max_entity_indirections, 40)
        with self.assertRaises(expat.ExpatError) as e:
            with open(self.xml_bomb, "rb") as f:
                p.ParseFile(f)
        self.assertEqual(str(e.exception), "entity indirection limit exceeded: line 7, column 6")

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
        self.assertEqual(str(e.exception), "document's entity expansion limit exceeded: line 6, column 6")

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
        self.assertEqual(str(e.exception), "document's entity expansion limit exceeded: line 6, column 6")

        p = expat.ParserCreate()
        p.max_entity_expansions = 1030 # 2 * x512 + 6
        p.Parse(xml)

        # test default limit of 8 MB
        xml = quadratic_bomb.replace(b"MARK", b"a" * 2 * 1024 ** 2)
        xml = xml.replace(b"<bomb>&a;</bomb>", b"<bomb>&c;</bomb>")
        p = expat.ParserCreate()
        with self.assertRaises(expat.ExpatError) as e:
            p.Parse(xml)
        self.assertEqual(str(e.exception), "document's entity expansion limit exceeded: line 6, column 6")

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

    def test_etree(self):
        with self.assertRaises(ET.ParseError) as e:
            ET.parse(self.xml_bomb)
        self.assertEqual(str(e.exception),
                         "entity indirection limit exceeded: line 7, column 6")

        eight_mb = 1024 ** 2 * 8
        with self.assertRaises(ET.ParseError) as e:
            xml = quadratic_bomb.replace(b"MARK", b"a" * (eight_mb + 1))
            ET.fromstring(xml)



def test_main():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(DefusedExpatTests))
    return suite

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(test_main())
    sys.exit(not result.wasSuccessful())
