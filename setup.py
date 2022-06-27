# todo: finish
# todo: create desktop shortcuts
import sys
import versioneer

from distutils.core import setup

if sys.version_info[:2] < (3, 7):
    raise Exception("You need Python 3.7+")

requirements = [
    "numpy",
    "scipy",
    "cython",
    "sipyco",
    "pyqt",
    "qt5reactor",
    "pyqtgraph",
    "twisted",
    "zope",
    "artiq-comtools",
    "pyvisa",
    "pyserial",
    "h5py",
    "hdf5"
]

console_scripts = [
    # "artiq_client = artiq.frontend.artiq_client:main",
    # todo: add labrad_master
    # todo: add labrad_node
]

gui_scripts = [
    # "artiq_browser = artiq.frontend.artiq_browser:main",
    # todo: add EGGS GUI
]

setup(
    name="EGGS_labrad",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author='Clayton Ho',
    author_email="claytonho@g.ucla.edu",
    url="https://github.com/EGGS-Experiment",
    description="Experimental Control System for the EGGS Experiment",
    long_description=open("README.rst", encoding="utf-8").read(),
    license="LGPLv3+",
    classifiers="""
        Development Status :: 5 - Production/Stable
        Environment :: Console
        Environment :: X11 Applications :: Qt
        Intended Audience :: Science/Research
        License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)
        Operating System :: Microsoft :: Windows
        Operating System :: POSIX :: Linux
        Programming Language :: Python :: 3.7
        Topic :: Scientific/Engineering :: Physics
        Topic :: System :: Hardware
        """.splitlines(),
    install_requires=requirements,
    extras_require={},
    packages=find_packages(),
    namespace_packages=[],
    include_package_data=True,
    ext_modules=[],
    entry_points={
        "console_scripts": console_scripts,
        "gui_scripts": gui_scripts,
    }
)
