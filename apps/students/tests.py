from django.test import TestCase

# Create your tests here.




class StudentTests(TestCase):

    def test_example(self):
        self.assertEqual(1 + 1, 2)

    def test_string_value(self):
        self.assertEqual("LearnMetricsAI", "LearnMetricsAI")

    def test_boolean_value(self):
        self.assertTrue(True)