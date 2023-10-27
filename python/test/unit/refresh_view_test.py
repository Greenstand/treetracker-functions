import sys
import unittest

from python.python_functions import refresh_view

print(sys.path)


class TestStringMethods(unittest.TestCase):
    def test_hello(self):
        self.assertEqual(refresh_view.hello('Chen'), 'Hello, Chen!')


# run test
if __name__ == '__main__':
    unittest.main()
