"""passbook allauth setup.py"""
from setuptools import setup

setup(
    name='django-allauth-passbook',
    version='0.2.6-beta',
    description='passbook support for django-allauth',
    # long_description='\n'.join(read_simple('docs/index.md')[2:]),
    long_description_content_type='text/markdown',
    author='BeryJu.org',
    author_email='hello@beryju.org',
    packages=['allauth_passbook'],
    include_package_data=True,
    install_requires=['django-allauth'],
    keywords='django allauth passbook',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Web Environment',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
    ],
)
