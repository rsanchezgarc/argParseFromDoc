import os

import setuptools
from setuptools import setup

VERSION="0.0.4"

def readme():
  readmePath = os.path.abspath(os.path.join(__file__, "..", "README.md"))
  try:
    with open(readmePath) as f:
      return f.read()
  except UnicodeDecodeError:
    try:
      with open(readmePath, 'r', encoding='utf-8') as f:
        return f.read()
    except Exception as e:
      return "Description not available due to unexpected error: "+str(e)


with open(os.path.abspath(os.path.join(os.path.dirname(__file__),"requirements.txt"))) as f:
    install_requires = [ line for line in f.readlines() if line and not line.startswith("#")]

setup(name='argParseFromDoc',
      version=VERSION,
      description='Simple argument parser for documented functions',
      long_description=readme(),
      long_description_content_type="text/markdown",
      keywords='argument parser ArgParser docstring argparse',
      url='https://github.com/rsanchezgarc/argParseFromDoc',
      author='Ruben Sanchez-Garcia',
      author_email='ruben.sanchez-garcia@stats.ox.ac.uk',
      license='Apache 2.0',
      packages=setuptools.find_packages(),
      install_requires=install_requires,
      dependency_links=[],
      include_package_data=True,
      zip_safe=False
)

