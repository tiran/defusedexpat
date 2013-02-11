============
defusedexpat
============

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


Requirements
============

* Python 2.6.6 or newer (2.6.8 for randomized hashing)
* Python 2.7.3 or newer
* Python 3.1.5 or newer
* Python 3.2.3 or newer
* Python 3.3.0 or newer


License
=======

Copyright (c) 2013 by Christian Heimes <christian@python.org>

Licensed to PSF under a Contributor Agreement.

See http://www.python.org/psf/license for licensing details.


Contributors
============

Antoine Pitrou <solipsis@pitrou.net>
  code review
