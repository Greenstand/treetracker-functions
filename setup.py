from setuptools import setup

setup(
    name='python_functions',
    version='1.0',
    description='Functions to be used in treetracker DAG',
    packages=['python_functions'],
    package_dir={'python_functions':'python/python_functions'},
    scripts=['python/scripts/ci.sh'],
)
