from setuptools import setup

setup(
    name='functions',
    version='1.0',
    description='Functions to be used in treetracker DAG',
    packages=['functions'],
    package_dir={'functions': 'python/functions'},
    scripts=['python/scripts/ci.sh'],
)
