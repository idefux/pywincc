from wincc_connect.__init__ import __version__
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
    description='wincc_connect: A wincc command line interface',
    author='Stefan Fuchs',
    url='https://github.com/Idefux/wincc_connect',
    install_requires=install_requires,
    name='wincc_connect',
    version=__version__,
    packages=find_packages(exclude=['docs', 'reports', 'venv', 'tests'])
#   py_modules=['wincc_connect', 'alarm', 'helper', 'interactive', 'mssql',
#               'operator_messages', 'parameter', 'report', 'tag',
#               'wincc_hosts', 'wincc'],
    ,
    entry_points='''
        [console_scripts]
        wincc_connect=wincc_connect.wincc_connect:cli
        wincc_hosts=wincc_connect.wincc_hosts:cli
    ''',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
                 ],
)
