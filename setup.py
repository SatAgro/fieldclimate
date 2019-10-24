from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='fieldclimate',
    version='1.1',
    install_requires=required,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    url='https://github.com/SatAgro/fieldclimate',
    description='A Python client for the Pessl Instruments GmbH RESTful API.',
)
