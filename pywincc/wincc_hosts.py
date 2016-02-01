"""command line interface for handling of wincc hosts

Hosts are stored in a file hosts.sav in root directory.
This module enables addind, listing and removing of hosts.

Example:
    $ python wincc_hosts.py list_hosts
    $ python wincc_hosts.py add_host AGRO --host-address \
    10.1.57.50\\WINCC -dn "AGRO ENERGIE SCHWYZ"
    $ python wincc_hosts.py remove_host AGRO
"""

from __future__ import print_function
import click
import logging
from .wincc import WinCCHosts, wincc


@click.group()
@click.option('--debug', default=False, is_flag=True, help='Turn on debug mode. \
Will print some debug messages.')
def cli(debug):
    """Main entry point for program.
    Turn on/off debug mode.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)


@cli.command()
@click.argument('hostname')
@click.option('--host-address', '-h', prompt=True,
              help='e.g. 10.1.57.50\\WINCC')
@click.option('--database', '-d', default='',
              help='WINCC runtime database name e.g. \
              CC_OS_1__15_09_01_08_20_14R')
@click.option('--descriptive-name', '-dn', default='',
              help='Optional more descriptive name for the host. Used in \
              report titles.')
def add_host(hostname, host_address, database, descriptive_name):
    """Add a host with given data to the list."""
    if not database:
        read_database_name = raw_input('Database name not given. Do you want '
                                       'me to connect to host and read the '
                                       'database name? (y/n)')
        if read_database_name == 'y':
            wincc_ = wincc(host_address, '')
            database = wincc_.fetch_wincc_database_name()
            wincc_.close()
        else:
            print("Database will not be stored along with hostname and \
            host-address.")

    hosts = WinCCHosts()
    hosts.add_host(hostname, host_address, database, descriptive_name)
    hosts.save_to_file()


@cli.command()
def list_hosts():
    """List all hosts stored in hosts.sav"""
    hosts = WinCCHosts()
    if hosts:
        for host in hosts:
            print(host)
    else:
        print("Could not find hosts.sav file.")


@cli.command()
@click.argument('hostname')
def remove_host(hostname):
    """Remove host with given hostname."""
    hosts = WinCCHosts()
    hosts.load_from_file()
    if hosts.remove_host(hostname):
        print("Host successfully removed from list.")
        hosts.save_to_file()
    else:
        print("Host could not be found.")


@cli.command()
@click.argument('hostname')
@click.argument('key_figures')
def add_key_figures(hostname, key_figures):
    """Return a list of key_figures connected to the host info."""
    hosts = WinCCHosts()
    print(key_figures)
    key_figures_dict = eval(key_figures)
    hosts.add_key_figures(hostname, key_figures_dict)
    for host in hosts:
        print(host)
    # hosts.save_to_file()


# @cli.command()
# def translate():
#     hosts = WinCCHosts()
#     hosts.save_as_class()
