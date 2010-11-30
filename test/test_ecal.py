#!/usr/bin/python

import unittest
import ecal


class MakeAddress(unittest.TestCase):
    def testModel(self):
        user1 = ecal.EcalUser()
        user2 = ecal.EcalUser()
        self.assertNotEqual(user1.email_address, user2.email_address)


if __name__ == "__main__":
    unittest.main()
