# Copyright (c) 2016 Nokia, Inc.
# All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# Copyright (c) 2016 Nokia, Inc.
# All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import time
import string

from nuage_shim.base import HandlerBase
from nuage_shim.utils import compute_netmask
from nuage_shim.utils import compute_network_addr
from nuage_shim.vm_split_activation import NUSplitActivation
from nuage_shim import model as Model


from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class NuageNetL3VPN(HandlerBase):

    def __init__(self, _api_url, _username, _password, _enterprise, _enterprise_name):
        self.api_url = _api_url
        self.username = _username
        self.password = _password
        self.enterprise = _enterprise
        self.enterprise_name = _enterprise_name

    def bind_port(self, uuid, model, changes):
        """ Called to bind port to VM.

        :param uuid: UUID of Port
        :param model: Model object
        :returns: dict of vif parameters (vif_type, vif_details)
        """
        LOG.info("bind_port: %s" % uuid)
        port = model.ports.get(uuid, None)
        if not port:
            LOG.error("Cannot find port")
            return dict()
        service_binding = model.vpn_ports.get(uuid, None)
        if not service_binding:
            LOG.error("Cannot bind port, not bound to a service")
            return dict()
        vpn_instance = model.vpn_instances.get(service_binding["vpn_instance"], None)
        if not vpn_instance:
            LOG.error("VPN instance not available!")
            return dict()
        rd_list = list()
        rd_string = vpn_instance.get("route_distinguishers")
        if rd_string:
            tmp_list = rd_string.split(',')
            for rd_name in tmp_list:
                rd_list.append(rd_name.strip())
        afconfig_list = list()
        afconfig_name_list = list()
        afconfig_string = vpn_instance.get("ipv4_family")
        if afconfig_string:
            tmp_list = afconfig_string.split(',')
            for afconfig_name in tmp_list:
                afconfig_name_list.append(afconfig_name.strip())
        LOG.info("port: %s" %  port)
        LOG.info("service: %s" %  vpn_instance)
        for afconfig_name in afconfig_name_list:
            afconfig = model.vpn_afconfigs.get(afconfig_name, None)
            if (afconfig):
                afconfig_list.append(afconfig)
                LOG.info("  afconfig(%s): %s" % (afconfig_name, afconfig))
        LOG.info("changes = %s" % changes)
        prefix = port.get('subnet_prefix', '32')
        print('prefix = %s' % prefix)
        if len(afconfig_list) > 0:
            rt = afconfig_list[0].get('vrf_rt_value')
        else:
            rt = vpn_instance.get("ipv4_family")
        net_address = str(compute_network_addr(port.get('ipaddress', ''), prefix))
        subnet_name = 'Subnet' + net_address.replace('.','_')
        if len(rd_list) > 0:
            rd = rd_list[0]
        else:
            rd = rt
        config = {
            'api_url': self.api_url,
            'domain_name': vpn_instance.get('vpn_instance_name'),
            'enterprise': self.enterprise,
            'enterprise_name': self.enterprise_name,
            'netmask': compute_netmask(prefix),
            'network_address': net_address,
            'route_distinguisher': rd,
            'route_target': rt,
            'subnet_name': subnet_name,
            'username': self.username,
            'password': self.password,
            'vm_ip': port.get('ipaddress', ''),
            'vm_mac': port.get('mac_address', ''),
            'vm_name': port.get('device_id', ''),  ## uuid of the VM
            'vm_uuid': port.get('device_id', ''),
            'vport_name': port.get('id', ''),
            'zone_name': 'Zone0',
            'tunnel_type': 'GRE',
            'domain_template_name': 'GluonDomainTemplate'
        }
        sa = NUSplitActivation(config)
        if sa.activate():
            retval = {'vif_type': 'ovs', 'vif_details': {'port_filter': False, 'bridge_name': 'alubr0'}}
        else:
            retval = dict()
        return retval

    def unbind_port(self, uuid, model, changes):
        """ Called to unbind port from VM.

        :param uuid: UUID of Port
        :param model: Model object
        :returns: None
        """
        LOG.info("unbind_port: %s" % uuid)
        port = model.ports.get(uuid, None)
        if not port:
            LOG.error("Cannot find port")
            return False
        LOG.info("port: %s" %  port)
        LOG.info("changes = %s" % changes)
        config = {
            'api_url': self.api_url,
            'enterprise': self.enterprise,
            'enterprise_name': self.enterprise_name,
            'username': self.username,
            'password': self.password,
            'vm_uuid': changes.prev.get('device_id', ''),
            'vport_name': port.get('id', '')
        }
        sa = NUSplitActivation(config)
        return sa.deactivate()

    def modify_port(self, uuid, model, changes):
        """ Called when attributes change on a bound port.

        :param uuid: UUID of Port
        :param model: Model object
        :param changes: dictionary of changed attributes
        :returns: None
        """
        LOG.info("modify_port: %s" % uuid)
        LOG.info("changes = %s" % changes)
        pass

    def delete_port(self, uuid, model):
        """ Called when a bound port is deleted

        :param uuid: UUID of Port
        :param model: Model object
        :param changes: dictionary of changed attributes
        :returns: None
        """
        pass

    def modify_service(self, uuid, model, changes):
        """ Called when attributes change on a service associated with a bound port.

        :param uuid: UUID of Service
        :param model: Model Object
        :param changes: dictionary of changed attributes
        :returns: None
        """
        LOG.info("modify_service: %s" % uuid)
        LOG.info("changes = %s" % changes)
        pass

    def delete_service(self, uuid, model, changes):
        """ Called when a service associated with a bound port is deleted

        :param uuid: UUID of Service
        :param model: Model Object
        :param changes: dictionary of changed attributes
        :returns: None
        """
        pass

    def modify_service_binding(self, uuid, model, prev_binding):
        """ Called when a service is associated with a bound port.

        :param uuid: UUID of Port
        :param model: Model Object
        :param prev_binding: dictionary of previous binding
        :returns: None
        """
        port = model.ports.get(uuid, None)
        if not port:
            LOG.error("Cannot find port")
            return False
        changes = Model.ChangeData()
        changes.prev["device_id"] = port.device_id
        LOG.info("modify_service_binding: %s" % uuid)
        LOG.info(prev_binding)
        if not self.unbind_port(uuid, model, changes):
            LOG.error("unbind failed")
        changes = Model.ChangeData()
        if not self.bind_port(uuid, model, changes):
            LOG.error("bind to new service failed")

    def delete_service_binding(self, model, prev_binding):
        """ Called when a service is disassociated with a bound port.

        :param model: Model Object
        :param prev_binding: dictionary of previous binding
        :returns: True if success, False otherwise
        """
        LOG.info("delete_service_binding:")
        LOG.info(prev_binding)
        uuid = prev_binding.get("id")
        if uuid:
            port = model.ports.get(uuid, None)
            if not port:
                LOG.error("Cannot find port")
                return False
            LOG.info("port: %s" % port)
            changes = Model.ChangeData()
            changes.prev["device_id"] = port.device_id
            if not self.unbind_port(uuid, model, changes):
                LOG.error("unbind failed")
            prefix = port.get('subnet_prefix', '32')
            print('prefix = %s' % prefix)
            rt = "65534:15655"
            rd = "65534:21953"
            net_address = str(compute_network_addr(port.get('ipaddress', ''),
                                                   prefix))
            subnet_name = 'Subnet' + net_address.replace('.', '_')
            config = {
                'api_url': self.api_url,
                'domain_name': "Domain0000",
                'enterprise': self.enterprise,
                'enterprise_name': self.enterprise_name,
                'netmask': compute_netmask(prefix),
                'network_address': net_address,
                'route_distinguisher': rd,
                'route_target': rt,
                'subnet_name': subnet_name,
                'username': self.username,
                'password': self.password,
                'vm_ip': port.get('ipaddress', ''),
                'vm_mac': port.get('mac_address', ''),
                'vm_name': port.get('device_id', ''),  ## uuid of the VM
                'vm_uuid': port.get('device_id', ''),
                'vport_name': port.get('id', ''),
                'zone_name': 'Zone0',
                'tunnel_type': 'GRE',
                'domain_template_name': 'GluonDomainTemplate'
            }
            sa = NUSplitActivation(config)
            return sa.activate()
        else:
            LOG.error("Bad UUID in prev_binding %s" % uuid)
            return False


    def modify_subport_parent(self, uuid, model, prev_parent, prev_parent_type):
        """ Called when a subport's parent relationship changes.

        :param uuid: UUID of Subport
        :param model: Model object
        :param prev_parent: UUID of previous parent
        :param prev_parent_type: name of previous parent (Port or Subport)
        :returns: None
        """
        pass

