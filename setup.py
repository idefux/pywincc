from pywincc.__init__ import __version__
from setuptools import setup, find_packages

install_requires = [
        'Click',
        'adodbapi',
        'pypiwin32',
        'py-dateutil',
        'jinja2',
        'joblib'
    ]

setup(
    description='pywincc: A wincc command line interface',
    author='Stefan Fuchs',
    url='https://github.com/Idefux/pywincc',
    install_requires=install_requires,
    name='pywincc',
    version=__version__,
    packages=find_packages(exclude=['docs', 'reports', 'venv', 'venv2', 'tests']),
    entry_points={
              'console_scripts': [
                                  'pywincc = pywincc.wincc_connect:cli',
                                  'wincc_hosts = pywincc.wincc_hosts:cli'
                                  ],
              },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
                 ],
)
