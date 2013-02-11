# defusedexpat
#
# Copyright (c) 2013 by Christian Heimes <christian@python.org>
# Licensed to PSF under a Contributor Agreement.
# See http://www.python.org/psf/license for licensing details.
"""Defused pyexpat and _elementtree helper
"""
__all__ = ("monkey_patch",)

import sys
import os
import imp

HERE = os.path.dirname(os.path.abspath(__file__))

def _load_module(modname):
    """Load the module from current directory

    In Python 3.x pyexpat and _elementtree are a builtin module. This hack
    overwrites the module.
    """
    if modname in sys.modules:
        raise ValueError("%s already loaded" % modname)
    try:
        fh, filename, description = imp.find_module(modname, [HERE])
        mod = imp.load_module(modname, fh, filename, description)
    finally:
        fh.close()
    modpath = getattr(sys.modules[modname], "__file__", "")
    if not modpath.startswith(HERE):
        raise ValueError("Unpatched module %r loaded (%s != %s)" %
                         (mod, moddir, HERE))
    return mod


pyexpat = _load_module("pyexpat")
_elementtree = _load_module("_elementtree")

_ExpatParser_orig__init__ = None


def _ExpatParser_patched__init__(self, *args, **kwargs):
    _orig__init__(self, *args, **kwargs)
    self._external_ges = 0


def monkey_patch():
    global _ExpatParser_orig__init__

    from xml.sax.expatreader import ExpatParser
    from xml.dom.xmlbuilder import Options

    if _ExpatParser_orig__init__ is None:
        _ExpatParser_orig__init__ = ExpatParser.__init__

    ExpatParser.__int__ = _ExpatParser_patched__init__
    DomOptions.external_dtd_subset = False
    DomOptions.external_general_entities = False
    DomOptions.external_parameter_entities = False

monkey_patch()
