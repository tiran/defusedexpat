============
defusedexpat
============


.. contents:: Table of Contents
   :depth: 2

defusedexpat protects the XML packages of Python's standard library from
several denial of service vulnerabilities and external entity exploits. It
contains

* a modified and enhanced version of expat parser library

* replacements for pyexpat and cElementTree's _elementtree extension modules

* loader code that replaces built-in extensions with the modified extensions

* monkey patches for xml.sax and xml.dom to prevent external entity expansions

In order to protect your application you have to import the ``defusedxml``
module **before** any of the stdlib's XML modules.


Countermeasures
===============

* limited entity expansion level to antagonize billion laugh attacks

* limited total length of expansions to prevent quadratic blowups

* monkey patch to prevent retrieval of external entities and DTDs


Modifications
=============

Modifications in pyexpat
------------------------

Parser object
..............

New parser attributes (r/w)

* max_entity_indirections
* max_entity_expansions
* reset_dtd


Module constants
................

* XML_DEFAULT_MAX_ENTITY_INDIRECTIONS
* XML_DEFAULT_MAX_ENTITY_EXPANSIONS
* XML_BOMB_PROTECTION


Modules functions
..................

* get_reset_dtd(), set_reset_dtd(bool)
* get_max_entity_expansions(), set_max_entity_expansions(int)
* get_max_entity_indirections(), et_max_entity_indirections(int)


New CAPI members
................

* capi.GetFeature
* capi.SetFeature
* capi.GetFeatureDefault
* capi.SetFeatureDefault


Modifications in _elementtree
-----------------------------

_elementtree.XMLParser
.......................

New arguments and r/o attributes

* max_entity_indirections
* max_entity_expansions
* ignore_dtd


Modifications in expat
----------------------

new definitions::

  XML_BOMB_PROTECTION
  XML_DEFAULT_MAX_ENTITY_INDIRECTIONS
  XML_DEFAULT_MAX_ENTITY_EXPANSIONS
  XML_DEFAULT_RESET_DTD

new XML_FeatureEnum members::

  XML_FEATURE_MAX_ENTITY_INDIRECTIONS
  XML_FEATURE_MAX_ENTITY_EXPANSIONS
  XML_FEATURE_IGNORE_DTD

new XML_Error members::

  XML_ERROR_ENTITY_INDIRECTIONS
  XML_ERROR_ENTITY_EXPANSION

new API functions::

  int XML_GetFeature(XML_Parser parser,
                     enum XML_FeatureEnum feature,
                     long *value);
  int XML_SetFeature(XML_Parser parser,
                     enum XML_FeatureEnum feature,
                     long value);
  int XML_GetFeatureDefault(enum XML_FeatureEnum feature,
                            long *value);
  int XML_SetFeatureDefault(enum XML_FeatureEnum feature,
                            long value);

XML_FEATURE_MAX_ENTITY_INDIRECTIONS
   Limit the amount of indirections that are allowed to occur during the
   expansion of a nested entity. A counter starts when an entity reference
   is encountered. It resets after the entity is fully expanded. The limit
   protects the parser against exponential entity expansion attacks (aka
   billion laughs attack). When the limit is exceeded the parser stops and
   fails with `XML_ERROR_ENTITY_INDIRECTIONS`.
   A value of 0 disables the protection.

   Supported range
     0 .. UINT_MAX
   Default
     40

XML_FEATURE_MAX_ENTITY_EXPANSIONS
   Limit the total length of all entity expansions throughout the entire
   document. The lengths of all entities are accumulated in a parser variable.
   The setting protects against quadratic blowup attacks (lots of expansions
   of a large entity declaration). When the sum of all entities exceeds
   the limit, the parser stops and fails with `XML_ERROR_ENTITY_EXPANSION`.
   A value of 0 disables the protection.

   Supported range
     0 .. UINT_MAX
   Default
     8 MiB

XML_FEATURE_RESET_DTD
   Reset all DTD information after the <!DOCTYPE> block has been parsed. When
   the flag is set (default: false) all DTD information after the
   endDoctypeDeclHandler has been called. The flag can be set inside the
   endDoctypeDeclHandler. Without DTD information any entity reference in
   the document body leads to `XML_ERROR_UNDEFINED_ENTITY`.

   Supported range
     0, 1
   Default
     0


Requirements
============

* Python 2.6.6 or newer (2.6.8 for randomized hashing)
* Python 2.7.3 or newer
* Python 3.1.5 or newer
* Python 3.2.3 or newer
* Python 3.3.0 or newer


TODO
====

* Add functions to get and set default parser values


License
=======

Copyright (c) 2013 by Christian Heimes <christian@python.org>

Licensed to PSF under a Contributor Agreement.

See http://www.python.org/psf/license for licensing details.


Contributors
============

Antoine Pitrou
  code review

Brett Cannon
  code review
