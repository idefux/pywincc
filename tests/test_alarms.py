import unittest
from alarm import alarm_query_builder


class TestAlarmModule(unittest.TestCase):

    def test_alarm_query_builder(self):
        self.assertEqual(alarm_query_builder("2015-08-24 10:07:48", "2015-08-24 10:08:12", '', False, ''),
                         u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE MsgNr < 12508141 AND DateTime > '2015-08-24 08:07:48' AND DateTime < '2015-08-24 08:08:12'")


if __name__ == "__main__":
    unittest.main()
