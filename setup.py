# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages

setup(
    name='python-property-mapper',
    packages=find_packages(),
    version='0.1',
    author='Artem Vlasov',
    author_email='root@proscript.ru',
    url='http://github.com/Yuego/python-property-mapper/',
    license='MIT License, see LICENSE',
    description="Python dict to object property mapper",
    long_description=open('README.md').read(),
    zip_safe=False,
    install_requires=[],
    include_package_data=True,
    keywords=[],
    classifiers=[
        'Development Status :: 1 - Unstable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
