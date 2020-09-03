from setuptools import setup, find_packages
from os import path


package_name = "cerestim_dbs"
here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get the version number from the version file
# Versions should comply with PEP440.  For a discussion on single-sourcing
# the version across setup.py and the project code, see
# https://packaging.python.org/en/latest/single_source_version.html
__version__ = None
with open(path.join(package_name, "version.py")) as f:
    exec(f.read())  # Sets __version__ in setup namespace


setup(
    name=package_name,
    version=__version__,
    packages=find_packages() + ['cerestim_dbs/icons'],
    package_data={"cerestim_dbs/icons": ["*.png"]},
    description='Graphical interface to Blackrock Cerestim96 designed for use in MER',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Chadwick Boulay',
    author_email='chadwick.boulay@gmail.com',
    url='https://github.com/SachsLab/CereStimDBS',
    license='GPL v3',

    entry_points={
        'gui_scripts': ['dbs-stim=cerestim_dbs.CerestimGUI:main',
                        ],
    }
)
