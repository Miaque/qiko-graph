import unittest

from configs import qiko_configs


class ConfigTestCase(unittest.TestCase):
    def test_something(self):
        api_key = qiko_configs.ONE_API_KEY
        assert api_key is not None  # add assertion here


if __name__ == "__main__":
    unittest.main()
