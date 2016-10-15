import unittest
import etcd

from nuage_shim.utils import compute_network_addr, compute_netmask

class MyTestCase(unittest.TestCase):
    def test_compute_network_addr(self):
        ip_addr = '10.10.20.30'
        expected_net_addr = '10.10.16.0'
        net_addr = compute_network_addr("10.10.20.30", 20)
        self.assertEqual(expected_net_addr, net_addr)

    def test_compute_netmask(self):
        prefix = 16
        expected_netmask = '255.255.0.0'
        netmask = compute_netmask(prefix)
        self.assertEqual(expected_netmask, netmask)



if __name__ == '__main__':
    unittest.main()