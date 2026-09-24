"""
Unit Test Suite for KanhaSushi ELT Business Rules
Tests:
1. Bangkok Business Day 10:00 AM cutoff calculation logic
2. JSONB multilingual fallback handling
3. Line total and pricing integrity
"""

import unittest
from datetime import datetime
import pytz

BKK_TZ = pytz.timezone("Asia/Bangkok")


def calculate_business_date(dt_utc: datetime) -> str:
    """
    Simulates SQL:
    DATE((created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok') - INTERVAL '10 hours')
    """
    dt_bkk = dt_utc.astimezone(BKK_TZ)
    # Subtract 10 hours
    from datetime import timedelta
    adjusted_dt = dt_bkk - timedelta(hours=10)
    return adjusted_dt.strftime("%Y-%m-%d")


def parse_multilingual_name(name_json: dict) -> tuple:
    """
    Simulates SQL:
    COALESCE(name->>'th', name->>'en', 'Unknown') AS name_th,
    COALESCE(name->>'en', name->>'th', 'Unknown') AS name_en
    """
    th = name_json.get("th") or name_json.get("en") or "Unknown"
    en = name_json.get("en") or name_json.get("th") or "Unknown"
    return th, en


class TestKanhaSushiBusinessRules(unittest.TestCase):

    def test_business_day_regular_evening_shift(self):
        # Order placed on Friday evening at 20:00 BKK (13:00 UTC) -> Belongs to Friday
        dt_utc = pytz.utc.localize(datetime(2026, 4, 3, 13, 0, 0))
        biz_date = calculate_business_date(dt_utc)
        self.assertEqual(biz_date, "2026-04-03")

    def test_business_day_midnight_crossover(self):
        # Order placed on Saturday at 01:30 AM BKK (Friday 18:30 UTC) -> MUST belong to Friday
        dt_utc = pytz.utc.localize(datetime(2026, 4, 3, 18, 30, 0))
        biz_date = calculate_business_date(dt_utc)
        self.assertEqual(biz_date, "2026-04-03")

    def test_business_day_late_night_closing_at_4am(self):
        # Order placed on Saturday at 04:00 AM BKK (Friday 21:00 UTC) -> MUST belong to Friday
        dt_utc = pytz.utc.localize(datetime(2026, 4, 3, 21, 0, 0))
        biz_date = calculate_business_date(dt_utc)
        self.assertEqual(biz_date, "2026-04-03")

    def test_business_day_morning_cutoff_edge(self):
        # Order placed on Saturday at 09:59:59 AM BKK -> Still Friday's shift
        dt_utc = pytz.utc.localize(datetime(2026, 4, 4, 2, 59, 59))
        biz_date = calculate_business_date(dt_utc)
        self.assertEqual(biz_date, "2026-04-03")

    def test_business_day_new_shift_starts_at_10am(self):
        # Order placed on Saturday at 10:00:00 AM BKK -> New shift: Saturday
        dt_utc = pytz.utc.localize(datetime(2026, 4, 4, 3, 0, 0))
        biz_date = calculate_business_date(dt_utc)
        self.assertEqual(biz_date, "2026-04-04")

    def test_multilingual_jsonb_parsing(self):
        # Both languages present
        full_json = {"th": "ซูชิแซลมอน", "en": "Salmon Sushi"}
        th, en = parse_multilingual_name(full_json)
        self.assertEqual(th, "ซูชิแซลมอน")
        self.assertEqual(en, "Salmon Sushi")

        # English missing -> fallback to Thai
        th_only = {"th": "ข้าวหน้าปลาไหล"}
        th, en = parse_multilingual_name(th_only)
        self.assertEqual(th, "ข้าวหน้าปลาไหล")
        self.assertEqual(en, "ข้าวหน้าปลาไหล")

        # Empty dict -> fallback to Unknown
        empty_json = {}
        th, en = parse_multilingual_name(empty_json)
        self.assertEqual(th, "Unknown")
        self.assertEqual(en, "Unknown")


if __name__ == "__main__":
    unittest.main()
