from setuptools import setup

setup(
    name='wincc_connect',
    version='0.1',
#   py_modules=['wincc_connect', 'alarm', 'helper', 'interactive', 'mssql',
#               'operator_messages', 'parameter', 'report', 'tag',
#               'wincc_hosts', 'wincc'],
    install_requires=[
        'Click',
        'adodbapi',
        'pypiwin32',
        'py-dateutil',
        'jinja2'
    ],
    entry_points='''
        [console_scripts]
        wincc_connect=wincc_connect.wincc_connect:cli
        wincc_hosts=wincc_connect.wincc_hosts:cli
    ''',
)
