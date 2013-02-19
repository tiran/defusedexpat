#!/usr/bin/env python
import sys
import os
import subprocess
from glob import glob
from distutils.core import setup, Command
from distutils.extension import Extension


class TestCommand(Command):
    """Hack for setup.py with implicit build_ext -i
    """
    user_options = []

    def initialize_options(self):
        self.rootdir = os.getcwd()

    def finalize_options(self):
        pass

    def remove_ext(self):
        """Remove extensions

        All Python 2.x versions share the same library name. Remove the
        file to fix version mismatch errors.
        """
        for fname in os.listdir(self.rootdir):
            if fname.endswith(("so", "dylib", "pyd", "sl")):
                os.unlink(os.path.join(self.rootdir, fname))

    def get_lib_dirs(self):
        """Get version, platform and configuration dependend lib dirs

        Distutils caches the build command object on the distribution object.
        We can retrieve the object to retrieve the paths to the directories
        inside the build directory.
        """
        build = self.distribution.command_obj["build"]
        builddirs = set()
        for attrname in 'build_platlib', 'build_lib', 'build_purelib':
            builddir = getattr(build, attrname, None)
            if not builddir:
                continue
            builddir = os.path.abspath(os.path.join(self.rootdir, builddir))
            if not os.path.isdir(builddir):
                continue
            builddirs.add(builddir)
        return builddirs

    def run(self):
        self.remove_ext()
        # force a build with build_ext
        self.run_command("build")
        # get lib dirs from build object
        libdirs = self.get_lib_dirs()
        # add lib dirs to Python's search path
        env = os.environ.copy()
        env["PYTHONPATH"] = env["DEFUSED_EXPAT"] = os.pathsep.join(libdirs)
        # and finally run the test command
        errno = subprocess.check_call([sys.executable, "tests.py"], env=env)
        raise SystemExit(errno)


moddir = "Modules%i%i" % sys.version_info[0:2]
exts = []
expat_inc = [os.path.join(os.getcwd(), 'expat')]
define_macros = [
    ('HAVE_EXPAT_CONFIG_H', '1'),
    #('XML_DEFAULT_MAX_ENTITY_INDIRECTIONS', '40'),
    #('XML_DEFAULT_MAX_ENTITY_EXPANSIONS', str(8*1024*1024)),
    #('XML_DTD_RESET_FLAG_DEFAULT', '0'),
]
if sys.platform == "win32":
    define_macros.extend([
        ("PYEXPAT_EXPORTS", "1"),
        ("HAVE_EXPAT_H", "1"),
        ("XML_NS", "1"),
        ("XML_DTD", "1"),
        ("BYTEORDER", "1234"),
        ("XML_CONTEXT_BYTES", "1024"),
        ("XML_STATIC", "1"),
        ("HAVE_MEMMOVE", "1"),
    ])

expat_lib = []
expat_sources = ['expat/xmlparse.c',
                 'expat/xmlrole.c',
                 'expat/xmltok.c']
expat_depends = ['expat/ascii.h',
                 'expat/asciitab.h',
                 'expat/expat.h',
                 'expat/expat_config.h',
                 'expat/expat_external.h',
                 'expat/internal.h',
                 'expat/latin1tab.h',
                 'expat/utf8tab.h',
                 'expat/xmlrole.h',
                 'expat/xmltok.h',
                 'expat/xmltok_impl.h',
                 os.path.join(moddir, 'pyexpat.h')
                 ]

exts.append(Extension('pyexpat',
                      define_macros=define_macros,
                      include_dirs=expat_inc,
                      libraries=expat_lib,
                      sources=[os.path.join(moddir, 'pyexpat.c')] + expat_sources,
                      depends=expat_depends,
                      ))


define_macros.append(('USE_PYEXPAT_CAPI', None))
exts.append(Extension('_elementtree',
                      define_macros=define_macros,
                      include_dirs=expat_inc,
                      libraries=expat_lib,
                      sources=[os.path.join(moddir, '_elementtree.c')],
                      depends=[os.path.join(moddir, 'pyexpat.c')] +
                          expat_sources + expat_depends,
                      ))



long_description = []
with open("README.txt") as f:
    long_description.append(f.read())
with open("CHANGES.txt") as f:
    long_description.append(f.read())

setup(
    name="defusedexpat",
    version="0.3",
    ext_modules=exts,
    py_modules=["defusedexpat"],
    cmdclass={"test": TestCommand},
    author="Christian Heimes",
    author_email="christian@python.org",
    maintainer="Christian Heimes",
    maintainer_email="christian@python.org",
    url="https://bitbucket.org/tiran/defusedexpat",
    download_url="http://pypi.python.org/pypi/defusedexpat",
    keywords="xml expat",
    platforms="POSIX, Windows",
    license="PSFL",
    description="XML bomb protection with modified expat parser",
    long_description="\n".join(long_description),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Python Software Foundation License",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: C",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        # "Programming Language :: Python :: 3.4",
        "Topic :: Text Processing :: Markup :: XML",
    ],
)
