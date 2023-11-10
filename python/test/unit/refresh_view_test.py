import unittest
from python.functions import refresh_view


class TestStringMethods(unittest.TestCase):
    def test_hello(self):
        self.assertEqual(refresh_view.hello('Chen'), 'Hello, Chen!')


# run test
if __name__ == '__main__':
    unittest.main()
