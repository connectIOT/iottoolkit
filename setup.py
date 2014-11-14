from setuptools import setup, find_packages

version = '0.1'

setup(
    name='iottoolkit',
    version=version,
    description="Reference implementation of the Smart Model API",
    long_description=open('README.md').read(),

    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[],
    keywords='IoT',
    author='Michael J Koster',
    url='',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    tests_require=[
        'nose',
    ],
    test_suite='nose.collector',
    install_requires=[
        'isodate',
        'mosquitto',
        'rdflib-rdfjson',
        'rdflib-jsonld',
    ],
    dependency_links=[
        'git+https://github.com/RDFLib/rdflib-rdfjson.git#egg=rdflib-rdfjson',
        'git+https://github.com/RDFLib/rdflib-jsonld.git#egg=rdflib-jsonld',
    ]
)
