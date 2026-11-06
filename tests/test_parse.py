import datetime
import unittest

import parse


class NormalizeAdiTimeTests(unittest.TestCase):
    def test_five_digit_value(self):
        self.assertEqual(parse.normalize_adi_time("92700"), "092700")

    def test_colon_format(self):
        self.assertEqual(parse.normalize_adi_time("7:09:00"), "070900")

    def test_timedelta(self):
        self.assertEqual(
            parse.normalize_adi_time(datetime.timedelta(seconds=7 * 3600 + 9 * 60)),
            "070900",
        )

    def test_invalid_value(self):
        self.assertEqual(parse.normalize_adi_time("927000"), "")

    def test_empty_value(self):
        self.assertEqual(parse.normalize_adi_time(""), "")
        self.assertEqual(parse.normalize_adi_time(None), "")


class NormalizeAdiDateTests(unittest.TestCase):
    def test_plain_date(self):
        self.assertEqual(parse.normalize_adi_date("20131011"), "20131011")

    def test_dashed_date(self):
        self.assertEqual(parse.normalize_adi_date("2013-10-11"), "20131011")

    def test_date_object(self):
        self.assertEqual(parse.normalize_adi_date(datetime.date(2013, 10, 11)), "20131011")

    def test_invalid_date(self):
        self.assertEqual(parse.normalize_adi_date("20130230"), "")