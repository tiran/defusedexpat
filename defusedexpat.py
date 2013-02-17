# defusedexpat
#
# Copyright (c) 2013 by Christian Heimes <christian@python.org>
# Licensed to PSF under a Contributor Agreement.
# See http://www.python.org/psf/license for licensing details.
"""Defused pyexpat and _elementtree helper
"""
__all__ = ("monkey_patch", "unmonkey_patch")

import sys
import os
import imp

HERE = os.path.dirname(os.path.abspath(__file__))

if "xml" in sys.modules:
    raise ImportError("'xml' package is already loaded.'defusedexpat' must "
                      "be loaded first.")

def _load_module(modname):
    """Load the module from current directory

    In Python 3.x pyexpat and _elementtree are a builtin module. This hack
    overwrites the module.
    """
    if modname in sys.modules:
        raise ImportError("Stock module %r already loaded" % modname)
    searchpath = [HERE]
    if "DEFUSED_EXPAT" in os.environ:
        # for unit testing
        searchpath.extend(os.environ["DEFUSED_EXPAT"].split(os.pathsep))
    fh = None
    try:
        fh, filename, description = imp.find_module(modname, searchpath)
        mod = imp.load_module(modname, fh, filename, description)
    finally:
        if fh is not None:
            fh.close()
    modpath = getattr(sys.modules[modname], "__file__", "")
    if not modpath.startswith(HERE):
        raise ValueError("Unpatched module %r loaded (%s != %s)" %
                         (mod, moddir, HERE))
    return mod


pyexpat = _load_module("pyexpat")
_elementtree = _load_module("_elementtree")

from xml.sax import expatreader as _expatreader
from xml.dom import xmlbuilder as _xmlbuilder

_OrigExpatParser = _expatreader.ExpatParser
_OrigOptions = _xmlbuilder.Options


class _PatchedExpatParser(_OrigExpatParser):
    def __init__(self, *args, **kwargs):
        _OrigExpatParser.__init__(self, *args, **kwargs)
        self._external_ges = 0


class _PatchedOptions(_OrigOptions):
    # These settings are never checked by any code path in xml.dom.
    external_dtd_subset = False
    external_general_entities = False
    external_parameter_entities = False


def monkey_patch():
    _expatreader.ExpatParser = _PatchedExpatParser
    _xmlbuilder.Options = _PatchedOptions

def unmonkey_patch():
    _expatreader.ExpatParser = _OrigExpatParser
    _xmlbuilder.Options = _OrigOptions

monkey_patch()
