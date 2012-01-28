#!/usr/bin/python

import unittest
import ecal


class MakeAddress(unittest.TestCase):
    def testModel(self):
        user1 = ecal.EcalUser()
        user2 = ecal.EcalUser()
        self.assertNotEqual(user1.email_address, user2.email_address)


class GetEnvironment(unittest.TestCase):
    def testInLocalEnv(self):
        env = ecal.get_environment(version='testing')
        self.assertEqual(env, {
                'base_url': 'http://localhost:8000',
                'secure_base_url': 'http://localhost:8000',
                'rsa_key': None })

    def testInStagingEnv(self):
        env = ecal.get_environment(version='staging')
        self.assertEqual(env, {
                'base_url': 'http://staging.myeventbot-hrd.appspot.com',
                'secure_base_url': 'http://staging.myeventbot-hrd.appspot.com',
                'rsa_key': None })

    def testInProdEnv(self):
        env = ecal.get_environment(version='master')
        self.assertEqual(env['base_url'], 'http://www.myeventbot.com')
        self.assertEqual(env['secure_base_url'], 'https://myeventbot-hrd.appspot.com')
        # can't really assert on rsa_key...


if __name__ == "__main__":
    unittest.main()
