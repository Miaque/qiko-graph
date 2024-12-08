import unittest

from configs import qiko_graph_config


class ConfigTestCase(unittest.TestCase):
    def test_something(self):
        api_key = qiko_graph_config.LLM_API_KEY
        assert api_key is not None  # add assertion here


if __name__ == "__main__":
    unittest.main()
