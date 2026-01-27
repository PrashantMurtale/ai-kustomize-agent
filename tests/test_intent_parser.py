import unittest
from src.agents.intent_parser import IntentParser

class TestIntentParser(unittest.TestCase):

    def setUp(self):
        self.parser = IntentParser()

    def test_fallback_parse_add_memory_limit(self):
        request = "Add memory limit 512Mi to all deployments"
        intent = self.parser._fallback_parse(request)
        self.assertEqual(intent['action'], 'add')
        self.assertEqual(intent['resource_type'], 'deployments')
        self.assertEqual(intent['target_field'], 'resources.limits.memory')

    def test_fallback_parse_update_image(self):
        request = "Update images from docker.io to ecr.aws"
        intent = self.parser._fallback_parse(request)
        self.assertEqual(intent['action'], 'update')
        self.assertEqual(intent['resource_type'], 'deployments')
        self.assertEqual(intent['target_field'], 'image')

    def test_fallback_parse_add_label(self):
        request = "Add label team=platform to services"
        intent = self.parser._fallback_parse(request)
        self.assertEqual(intent['action'], 'add')
        self.assertEqual(intent['resource_type'], 'services')
        self.assertEqual(intent['target_field'], 'labels')

    def test_fallback_parse_with_namespace(self):
        request = "Add memory limit 512Mi to all deployments in staging"
        intent = self.parser._fallback_parse(request)
        self.assertEqual(intent['namespace'], 'staging')

if __name__ == '__main__':
    unittest.main()
