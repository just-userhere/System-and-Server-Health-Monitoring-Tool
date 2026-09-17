"""Basic automated tests for ServerPulse.

Run with:  py -m unittest discover -s tests -v
Run from the ServerPulse/ directory.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import alerts
import monitor


class TestThresholds(unittest.TestCase):
    def test_classify_normal(self):
        self.assertEqual(alerts.classify_metric(50), "NORMAL")
        self.assertEqual(alerts.classify_metric(0), "NORMAL")
        self.assertEqual(alerts.classify_metric(69.9), "NORMAL")

    def test_classify_warning(self):
        self.assertEqual(alerts.classify_metric(70), "WARNING")
        self.assertEqual(alerts.classify_metric(75), "WARNING")
        self.assertEqual(alerts.classify_metric(84.9), "WARNING")

    def test_classify_critical(self):
        self.assertEqual(alerts.classify_metric(85), "CRITICAL")
        self.assertEqual(alerts.classify_metric(90), "CRITICAL")
        self.assertEqual(alerts.classify_metric(100), "CRITICAL")

    def test_classify_none(self):
        self.assertEqual(alerts.classify_metric(None), "UNKNOWN")

    def test_overall_health(self):
        self.assertEqual(alerts.overall_health(10, 20, 30), "HEALTHY")
        self.assertEqual(alerts.overall_health(75, 20, 30), "WARNING")
        self.assertEqual(alerts.overall_health(10, 90, 30), "CRITICAL")
        self.assertEqual(alerts.overall_health(75, 80, 95), "CRITICAL")
        # Missing metrics are ignored, never crash.
        self.assertEqual(alerts.overall_health(None, None, None), "HEALTHY")
        self.assertEqual(alerts.overall_health(None, 90, 10), "CRITICAL")


class TestFormatting(unittest.TestCase):
    def test_format_uptime(self):
        self.assertIn("Days", monitor.format_uptime(90061))
        self.assertIn("Hours", monitor.format_uptime(3661))
        self.assertIn("Minutes", monitor.format_uptime(60))
        self.assertEqual(monitor.format_uptime(None), "N/A")

    def test_format_bytes(self):
        self.assertEqual(monitor.format_bytes(None), "N/A")
        self.assertEqual(monitor.format_bytes(0), "0 B")
        self.assertIn("KB", monitor.format_bytes(2048))
        self.assertIn("GB", monitor.format_bytes(2 * 1024 ** 3))


class TestLiveMetrics(unittest.TestCase):
    def test_cpu_valid(self):
        value = monitor.get_cpu_usage(interval=0.1)
        self.assertTrue(value is None or 0.0 <= value <= 100.0)

    def test_memory_valid(self):
        mem = monitor.get_memory()
        for key in ("percent", "used", "available", "total"):
            self.assertIn(key, mem)
        if mem["percent"] is not None:
            self.assertTrue(0.0 <= mem["percent"] <= 100.0)
        if mem["total"] is not None:
            self.assertGreater(mem["total"], 0)

    def test_disk_valid(self):
        disk = monitor.get_disk()
        for key in ("percent", "used", "free", "total"):
            self.assertIn(key, disk)
        if disk["percent"] is not None:
            self.assertTrue(0.0 <= disk["percent"] <= 100.0)

    def test_uptime(self):
        seconds = monitor.get_uptime_seconds()
        self.assertTrue(seconds is None or seconds >= 0)

    def test_system_info(self):
        info = monitor.get_system_info()
        for key in ("hostname", "os", "platform", "python_version"):
            self.assertIn(key, info)
            self.assertTrue(info[key])

    def test_top_processes(self):
        procs = monitor.get_top_processes(count=5)
        self.assertIsInstance(procs, list)
        self.assertLessEqual(len(procs), 5)


if __name__ == "__main__":
    unittest.main()
