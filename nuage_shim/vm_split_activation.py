# -*- coding: utf-8 -*-
# Copyright (c) 2016, Nokia
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the copyright holder nor the names of its contributors
#       may be used to endorse or promote products derived from this software without
#       specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Contains a class and main program for split activation of VMs in Nuage.

--- Author ---
Kamal Hussain <kamal.hussain@nokia.com>

--- Version history ---
2016-06-23 - 0.1 - First version
2016-06-26 - 0.2 - Change from fetch() to get_first(). Renaming class and file names

--- Usage ---
Create config file with right parameters
run 'python vm_split_activation.py -c <config-file> -v

"""

import argparse
import ConfigParser

from vspk import v3_2 as vsdk
import logging

logger = logging.getLogger(__name__)


class NUSplitActivation:
    def __init__(self, config):
        for k, v in config.items():
            setattr(self, k, v)

        try:
            self.session = vsdk.NUVSDSession(username=self.username, password=self.password,
                                             enterprise=self.enterprise, api_url=self.api_url)

            logger.info("starting session username: %s, password: %s, enterprise: %s, api_url: %s" % (
                self.username, self.password, self.enterprise, self.api_url))
            self.session.start()

        except Exception, e:
            logger.error("creating VSD session failed with error %s" % str(e))

    def deactivate(self):
        """
        deactivate VM
        :return:
        """
        try:
            vm = self.session.user.vms.get_first(filter='UUID== "%s"' % self.vm_uuid)

            for interface in vm.vm_interfaces.get():
                if interface.vport_name == self.vport_name:
                    vport = vsdk.NUVPort(id=interface.vport_id)
                    # vport.fetch()
                    vm.delete()
                    vport.delete()

        except Exception as e:
            logger.critical("Error on vm and vport deletion %s" % str(e));

        return

    def activate(self):
        """activate a VM
        """
        try:
            # get enterprise
            enterprise = self.session.user.enterprises.get_first(filter='name == "%s"' % self.enterprise_name)

            if enterprise is None:
                logger.critical("Enterprise %s not found, exiting" % enterprise)
                print "can't find enterprise"
                return False

            # get domains
            enterprise.domains.fetch()

            domain = next((domain for domain in enterprise.domains if
                           domain.route_distinguisher == self.route_distinguisher and domain.route_target == self.route_target),
                          None)

            if domain is None:
                logger.info("Domain %s not found, creating domain" % self.domain_name)

                domain_template = enterprise.domain_templates.get_first(filter='name == "%s"' % self.domain_template_name)
                domain = vsdk.NUDomain(name=self.domain_name,
                                       template_id=domain_template.id)
                enterprise.create_child(domain)

                # update domain with the right values
                domain.tunnel_type = self.tunnel_type
                domain.route_distinguisher = self.route_distinguisher
                domain.route_target = self.route_target
                domain.back_haul_route_target = '20000:20000'
                domain.back_haul_route_distinguisher = '20000:20000'
                domain.back_haul_vnid = '25000'
                domain.save()

            # get zone
            zone = domain.zones.get_first(filter='name == "%s"' % self.zone_name)

            if zone is None:
                logger.info("Zone %s not found, creating zone" % self.zone_name)

                zone = vsdk.NUZone(name=self.zone_name)
                domain.create_child(zone)

            zone.subnets.fetch()

            subnet = next((subnet for subnet in zone.subnets if
                           subnet.address == self.network_address and subnet.netmask == self.netmask), None)
            # get subnet
            # subnet = zone.subnets.get_first(filter='address == "%s"' % self.network_address)

            if subnet is None:
                logger.info("Subnet %s not found, creating subnet" % self.subnet_name)

                subnet = vsdk.NUSubnet(name=self.subnet_name, address=self.network_address,
                                       netmask=self.netmask)
                zone.create_child(subnet)

            # get vport
            vport = subnet.vports.get_first(filter='name == "%s"' % self.vport_name)

            if vport is None:
                # create vport
                logger.info("Vport %s is not found, creating Vport" % self.vport_name)

                vport = vsdk.NUVPort(name=self.vport_name, address_spoofing='INHERITED', type='VM',
                                     description='Automatically created, do not edit.')
                subnet.create_child(vport)

            # get vm
            vm = self.session.user.fetcher_for_rest_name('vm').get('uuid=="%s"' % self.vm_uuid)

            if not vm:
                logger.info("VM %s is not found, creating VM" % self.vm_name)

                vm = vsdk.NUVM(name=self.vm_name, uuid=self.vm_uuid, interfaces=[{
                    'name': self.vm_name,
                    'VPortID': vport.id,
                    'MAC': self.vm_mac,
                    'IPAddress': self.vm_ip
                }])

                self.session.user.create_child(vm)

            return True

        except Exception, e:
            logger.error("activating vm failed with exception %s" % str(e))

    def activate_by_name(self):
        """activate vm. Uses names to identify domain, subnet, and vm
        """

        # get enterprise
        enterprise = self.session.user.enterprises.get_first(filter='name == "%s"' % self.enterprise_name)

        if enterprise is None:
            logger.critical("Enterprise %s not found, exiting" % enterprise)
            print "can't find enterprise"
            return False

        # get domains
        domain = enterprise.domains.get_first(filter='name == "%s"' % self.domain_name)

        if domain is None:
            logger.info("Domain %s not found, creating domain" % self.domain_name)

            domain = vsdk.NUDomain(name=self.domain_name, route_target=self.route_target,
                                   route_distinguisher=self.route_distinguisher, template_id=self.domain_template_id)
            enterprise.create_child(domain)

        # get zone
        zone = domain.zones.get_first(filter='name == "%s"' % self.zone_name)

        if zone is None:
            logger.info("Zone %s not found, creating zone" % self.zone_name)

            zone = vsdk.NUZone(name=self.zone_name)
            domain.create_child(zone)

        # get subnet
        subnet = zone.subnets.get_first(filter='name == "%s"' % self.subnet_name)

        if subnet is None:
            logger.info("Subnet %s not found, creating subnet" % self.subnet_name)

            subnet = vsdk.NUSubnet(name=self.subnet_name, address=self.network_address,
                                   netmask=self.netmask)
            zone.create_child(subnet)

        # get vport
        vport = subnet.vports.get_first(filter='name == "%s"' % self.vport_name)

        if vport is None:
            # create vport
            logger.info("Vport %s is not found, creating Vport" % self.vport_name)

            vport = vsdk.NUVPort(name=self.vport_name, address_spoofing='INHERITED', type='VM',
                                 description='Automatically created, do not edit.')
            subnet.create_child(vport)

        # get vm
        vm = self.session.user.vms.get_first(filter='name == "%s"' % self.vm_name)
        # vm = self.session.user.fetcher_for_rest_name('vm').get('name=="%s"' % self.vm_name)

        if not vm:
            logger.info("VM %s is not found, creating VM" % self.vm_name)

            vm = vsdk.NUVM(name=self.vm_name, uuid=self.vm_uuid, interfaces=[{
                'name': self.vm_name,
                'VPortID': vport.id,
                'MAC': self.vm_mac,
                'IPAddress': self.vm_ip
            }])

            self.session.user.create_child(vm)

        return True


def getargs():
    parser = argparse.ArgumentParser(description='Create Gluon ports.')

    parser.add_argument('-d', '--debug', required=False, help='Enable debug output', dest='debug',
                        action='store_true')
    parser.add_argument('-c', '--config-file', required=False, help='configuration file',
                        dest='config_file', type=str)
    parser.add_argument('-r', '--remove', required=False, help='deactivate VM',
                        dest='deactivate', action='store_true')
    parser.add_argument('-v', '--verbose', required=False, help='Enable verbose output', dest='verbose',
                        action='store_true')

    args = parser.parse_args()
    return args


def parse_config_file(config_file):
    """ read configuration file """
    parser = ConfigParser.ConfigParser()

    parser.read(config_file)

    config = {}

    for section in parser.sections():
        for name, value in parser.items(section):
            config[name] = value
            logger.info("config key %s has value %s" % (name, value))

    return config


def main():
    """ main program to test the GluonPort. Usage
    python vm_split_activation.py -c <config file> -v
    """
    args = getargs()

    if args.config_file:
        config_file = args.config_file
        config = parse_config_file(config_file)

    else:
        config = {
            'api_url': '',
            'domain_name': '',
            'enterprise': '',
            'enterprise_name': '',
            'netmask': '',
            'network_address': '',
            'password': '',
            'route_distinguisher': '',
            'route_target': '',
            'subnet_name': '',
            'username': '',
            'vm_ip': '',
            'vm_mac': '',
            'vm_name': '',
            'vm_uuid': '',
            'vport_name': '',
            'zone_name': '',
        }

    if args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    logger.setLevel(log_level)

    gp = NUSplitActivation(config)

    if args.deactivate:
        if gp.deactivate():
            logger.info('VM successfully deactivated')

        else:
            logger.info("VM deactivation failed")
    else:
        if gp.activate():
            logger.info('VM successfully activated')

        else:
            logger.info("VM activation failed")


if __name__ == "__main__":
    main()
