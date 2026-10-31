import unittest

from eurocode3_teacher.engine import ConnectionData, MemberData, analyze


class EngineTest(unittest.TestCase):
    def test_member_and_bolted_connection(self):
        member = MemberData(5000, 8e7, 2e7, 4e5, 1.5e5, 3000, 3000, -100, 20, 5, 15)
        result = analyze(member, ConnectionData("براغي", 15, 4, 16, plate_thickness_mm=10, edge_mm=40, pitch_mm=70))
        self.assertGreaterEqual(len(result.findings), 7)
        self.assertEqual(result.missing, [])


if __name__ == "__main__":
    unittest.main()
