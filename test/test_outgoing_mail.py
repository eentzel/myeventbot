import unittest
import outgoing_mail

class MockMessage:
    def __init__(self, headers):
        self.original = headers

class TestConstructReferences(unittest.TestCase):
    def testNoMessageID(self):
        message = MockMessage({})
        self.assertEqual(outgoing_mail.construct_references(message), None)

    def testMessageIDButNoReferences(self):
        message = MockMessage({'Message-ID': '<DEADBEEF@example.com>'})
        self.assertEqual(outgoing_mail.construct_references(message), "<DEADBEEF@example.com>")

    def testMessageIDAndOneReference(self):
        message = MockMessage({
                'Message-ID': '<CHILD@example.com>',
                'References': '<PARENT@example.com>',
                })
        self.assertEqual(outgoing_mail.construct_references(message), "<PARENT@example.com> <CHILD@example.com>")

    def testMessageIDAndManyReferences(self):
        message = MockMessage({
                'Message-ID': '<CHILD@example.com>',
                'References': '<GGP@example.com> <GRANDPARENT@example.com> <PARENT@example.com>',
                })
        self.assertEqual(outgoing_mail.construct_references(message), "<GGP@example.com> <GRANDPARENT@example.com> <PARENT@example.com> <CHILD@example.com>")
