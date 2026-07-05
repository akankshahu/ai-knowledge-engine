import unittest
from backend.app.observability import REQUEST_COUNTS, REQUEST_LATENCY_SECONDS, record_request, render_metrics_text


class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        REQUEST_COUNTS.clear()
        REQUEST_LATENCY_SECONDS.clear()

    def test_record_request_updates_counters(self):
        record_request("/", 0.123)
        record_request("/", 0.200)
        record_request("/metrics", 0.050)

        self.assertEqual(REQUEST_COUNTS["/"], 2)
        self.assertAlmostEqual(REQUEST_LATENCY_SECONDS["/"], 0.323, places=3)
        self.assertEqual(REQUEST_COUNTS["/metrics"], 1)

    def test_render_metrics_text_contains_expected_lines(self):
        record_request("/", 0.1)
        metrics = render_metrics_text()
        self.assertIn('app_requests_total{path="/"} 1', metrics)
        self.assertIn('app_request_latency_seconds_total{path="/"} 0.100000', metrics)


if __name__ == "__main__":
    unittest.main()
