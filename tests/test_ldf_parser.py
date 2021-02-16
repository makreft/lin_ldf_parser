import unittest
from lin_ldf_parser import *


class LDFParserTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.ldf = LDFParser("dummy_ldf_for_tests.ldf")
        self.ldf.parse_all()
        self.ldf_empty = LDFParser("empty.ldf")
        self.ldf_dummy_dict = ldf_dict()

    def test_ldf_parse_all(self):

        pass


if __name__ == '__main__':
    unittest.main()
