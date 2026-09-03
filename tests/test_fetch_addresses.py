import json
import unittest
import urllib.error
import urllib.parse
from unittest.mock import patch

from scripts import fetch_addresses


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class RunOverpassQueryTests(unittest.TestCase):
    def test_posts_form_encoded_query_with_identifying_user_agent(self):
        query = '[out:json];node["addr:housenumber"](34.8,-119.2,34.9,-119.1);out;'

        with patch.object(
            fetch_addresses.urllib.request,
            "urlopen",
            return_value=_Response({"elements": []}),
        ) as urlopen:
            result = fetch_addresses._run_overpass_query(query)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, fetch_addresses.OVERPASS_URL)
        self.assertEqual(
            request.get_header("Content-type"),
            "application/x-www-form-urlencoded",
        )
        self.assertEqual(request.get_header("User-agent"), fetch_addresses.USER_AGENT)
        self.assertEqual(
            urllib.parse.parse_qs(request.data.decode()),
            {"data": [query]},
        )
        self.assertEqual(urlopen.call_args.kwargs["timeout"], fetch_addresses.REQUEST_TIMEOUT)
        self.assertEqual(result, {"elements": []})

    def test_retries_rate_limited_request(self):
        rate_limited = urllib.error.HTTPError(
            fetch_addresses.OVERPASS_URL,
            429,
            "Too Many Requests",
            None,
            None,
        )

        with (
            patch.object(
                fetch_addresses.urllib.request,
                "urlopen",
                side_effect=[rate_limited, _Response({"elements": []})],
            ) as urlopen,
            patch.object(fetch_addresses.time, "sleep") as sleep,
        ):
            result = fetch_addresses._run_overpass_query("[out:json];out;")

        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(fetch_addresses.RETRY_WAIT)
        self.assertEqual(result, {"elements": []})
