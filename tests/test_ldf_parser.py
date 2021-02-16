import unittest
from lin_ldf_parser import *


class LDFParserTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.ldf = LDFParser("dummy_ldf_for_tests.ldf")
        self.ldf.parse_all()
        self.ldf_empty = LDFParser("empty.ldf")
        self.ldf_empty.parse_all()
        self.ldf_dummy_dict = ldf_dict()

    def test_ldf_frames(self):
        self.assertNotEqual(self.ldf.frames, self.ldf_empty.frames)

    def test_ldf_node_attributes(self):
        self.assertNotEqual(self.ldf.node_attributes, self.ldf_empty.node_attributes)

    def test_ldf_signals(self):
        self.assertNotEqual(self.ldf.signals, self.ldf_empty.signals)

    def test_ldf_signal_encoding_types(self):
        self.assertNotEqual(self.ldf.signal_encoding_types, self.ldf_empty.signal_encoding_types)

    def test_ldf_signal_node_attributes(self):
        self.assertNotEqual(self.ldf.node_attributes, self.ldf_empty.node_attributes)

    def test_ldf_signal_signal_representation(self):
        self.assertNotEqual(self.ldf.signal_representation, self.ldf_empty.signal_representation)

    def test_ldf_signal_schedule_tables(self):
        self.assertNotEqual(self.ldf.schedule_tables, self.ldf_empty.schedule_tables)

    def test_ldf_signal_diagnostic_signal(self):
        self.assertNotEqual(self.ldf.diagnostic_signals, self.ldf_empty.diagnostic_signals)


if __name__ == '__main__':
    unittest.main()
