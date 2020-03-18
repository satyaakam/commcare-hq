import re
from contextlib import contextmanager
from copy import deepcopy
from distutils.version import LooseVersion
from unittest import skip

from django.test import SimpleTestCase, TestCase

from jsonschema import validate
from mock import Mock, patch
from nose.tools import assert_equal, assert_true

from corehq.motech.dhis2.const import DHIS2_MAX_VERSION
from corehq.motech.dhis2.repeaters import Dhis2Repeater
from corehq.motech.requests import Requests

dhis2_version = "2.32.2"
api_version = re.match(r'2\.(\d+)', dhis2_version).group(1)

base_url = f"https://play.dhis2.org/{dhis2_version}/"
username = "admin"
password = "district"
domain_name = "test-domain"

timestamp_pattern = (r"^[0-9]{4}-[0-9]{2}-[0-9]{2}"
                     r"[ T][0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}$")  # e.g. "2016-01-12T09:10:26.986"
dhis2_id_pattern = r"^[a-zA-Z0-9]+$"  # e.g. "zDhUuAYrxNC"
te_schema = {
    "type": "object",
    "properties": {
        # A Tracked Entity instance has the following properties:
        "trackedEntityInstance": {"type": "string", "pattern": dhis2_id_pattern},
        "trackedEntityType": {"type": "string", "pattern": dhis2_id_pattern},
        "orgUnit": {"type": "string", "pattern": dhis2_id_pattern},
        "created": {"type": "string", "pattern": timestamp_pattern},
        "lastUpdated": {"type": "string", "pattern": timestamp_pattern},
        "inactive": {"type": "boolean"},
        "deleted": {"type": "boolean"},
        "featureType": {"type": "string"},
        "programOwners": {"type": "array"},
        "enrollments": {"type": "array"},
        "relationships": {"type": "array"},
        "attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    # Tracked Entities have attributes with the following properties:
                    "displayName": {"type": "string"},
                    "code": {"type": "string"},
                    "attribute": {"type": "string", "pattern": dhis2_id_pattern},
                    "valueType": {"type": "string"},
                    "value": {},  # Could be anything
                    "created": {"type": "string", "pattern": timestamp_pattern},
                    "lastUpdated": {"type": "string", "pattern": timestamp_pattern},
                }
            }
        }
    }
}
grid_schema = {
    "type": "object",
    "properties": {
        # A grid query response has the following properties:
        "width": {"type": "integer"},
        "height": {"type": "integer"},
        "metaData": {
            "type": "object",
            "properties": {
                # "metaData" is used to give names for IDs used in columns
                # (e.g. names for the IDs in the "Tracked entity type" column)
                "names": {"type": "object"},
            }
        },
        "headers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    # A grid query response describes headers in the following terms:
                    "column": {"type": "string"},  # e.g. "Tracked entity type"
                    "name": {"type": "string"},  # e.g. "te"
                    "type": {"type": "string"},  # e.g. "java.lang.String"
                    "hidden": {"type": "boolean"},
                    "meta": {"type": "boolean"},
                }
            }
        },
        "rows": {
            "type": "array",
            "items": {"type": "array"}
        }
    }
}

allen_town_health_post_ou = "kbGqmM6ZWWV"
last_name_attr_id = "zDhUuAYrxNC"
first_name_attr_id = "w75KJ2mc4zz"
address_attr_id = "VqEFza8wbwA"
city_attr_id = "FO4sWYJ64LQ"
gender_attr_id = "cejWyOfXge6"
person_te_type_id = "nEenWmSyUEp"


@skip  # Don't test DHIS2 API endpoints as part of CommCareHQ builds
class Dhis2ApiTests(SimpleTestCase):
    """
    These tests are for reference. They demonstrate the DHIS2 API calls
    relevant to Tracked Entity integration.
    """

    def setUp(self):
        self.requests = Requests(domain_name, base_url, username, password)

    @patch('corehq.motech.requests.RequestLog', Mock())
    def test_get_index(self):
        endpoint = f"/api/{api_version}/trackedEntityInstances"
        params = {"ou": allen_town_health_post_ou}
        response = self.requests.get(endpoint, params=params)

        _assert_status_2xx(response)
        instances = response.json()["trackedEntityInstances"]
        assert_true(instances)
        for te in instances:
            validate(te, te_schema)

    @patch('corehq.motech.requests.RequestLog', Mock())
    def test_query(self):
        last_name = "Pierce"
        endpoint = f"/api/{api_version}/trackedEntityInstances"
        params = {
            "ou": allen_town_health_post_ou,
            "filter": f"{last_name_attr_id}:EQ:{last_name}",
        }
        response = self.requests.get(endpoint, params=params)

        _assert_status_2xx(response)
        instances = response.json()["trackedEntityInstances"]
        assert_true(instances)
        assert_true(
            all(_is_attr_equal(te, last_name_attr_id, last_name) for te in instances),
            "Query results do not match query filter."
        )

    @patch('corehq.motech.requests.RequestLog', Mock())
    def test_grid_query(self):
        city = "Johannesburg"
        endpoint = f"/api/{api_version}/trackedEntityInstances/query"
        params = {
            "ou": allen_town_health_post_ou,
            "filter": f"{city_attr_id}:EQ:{city}",
            "attribute": [first_name_attr_id, last_name_attr_id],
            "skipPaging": 1,
        }
        response = self.requests.get(endpoint, params=params)

        _assert_status_2xx(response)
        grid = response.json()
        validate(grid, grid_schema)

    @patch('corehq.motech.requests.RequestLog', Mock())
    def test_create(self):
        endpoint = f"/api/{api_version}/trackedEntityInstances"
        json_data = {
            "trackedEntityType": person_te_type_id,
            "orgUnit": allen_town_health_post_ou,
            "attributes": [
                {"attribute": first_name_attr_id, "value": "Nelson"},
                {"attribute": last_name_attr_id, "value": "Mandela"},
                {"attribute": address_attr_id, "value": "De Tuynhuys"},
                {"attribute": city_attr_id, "value": "Cape Town"},
                {"attribute": gender_attr_id, "value": "Male"},
            ]
        }
        response = self.requests.post(endpoint, json=json_data)

        _assert_status_2xx(response)
        result = response.json()
        assert_equal(result["response"]["imported"], 1)
        tei_id = result["response"]["importSummaries"][0]["reference"]
        assert_true(
            re.match(dhis2_id_pattern, tei_id),
            f'Instance ID "{tei_id}" does not look like a DHIS2 ID',
        )
        tei_url = result["response"]["importSummaries"][0]["href"]
        assert_true(tei_url.startswith(base_url))

    @patch('corehq.motech.requests.RequestLog', Mock())
    def test_update(self):
        tei_id = "wrqfV2SkucE"
        with get_tracked_entity(self.requests, tei_id) as person:
            _update_attr(person, first_name_attr_id, "Nelson")
            _update_attr(person, last_name_attr_id, "Mandela")
            endpoint = f"/api/{api_version}/trackedEntityInstances/{tei_id}"

            response = self.requests.put(endpoint, json=person)
            _assert_status_2xx(response)

    @patch('corehq.motech.requests.RequestLog', Mock())
    def test_update_with_events(self):
        # TODO: test_update_with_events
        pass


def _is_attr_equal(entity, attr_id, value):
    return any(attr["attribute"] == attr_id and attr['value'] == value for attr in entity['attributes'])


def _update_attr(entity, attr_id, value):
    for attr in entity["attributes"]:
        if attr["attribute"] == attr_id:
            attr["value"] = value
            break
    else:
        entity["attributes"].append(
            {"attribute": attr_id, "value": value}
        )


def _assert_status_2xx(response):
    assert_true(
        200 <= response.status_code < 300,
        f"Service responded with status code {response.status_code}"
    )


@contextmanager
def get_tracked_entity(requests, te_id):
    """
    Context manager that resets a tracked entity instance
    """
    endpoint = f"/api/{api_version}/trackedEntityInstances/{te_id}"
    params = {"fields": "*"}  # Tells DHIS2 to return everything
    response = requests.get(endpoint, params=params)
    orig_data = response.json()
    try:
        yield deepcopy(orig_data)  # Make sure orig_data can't be changed
    finally:
        requests.put(endpoint, json=orig_data)


class ApiVersionTests(SimpleTestCase):

    def test_major_minor_patch(self):
        repeater = Dhis2Repeater.wrap({"dhis2_version": "2.31.6"})
        self.assertEqual(repeater.api_version, 31)

    def test_major_minor(self):
        repeater = Dhis2Repeater.wrap({"dhis2_version": "2.31"})
        self.assertEqual(repeater.api_version, 31)

    def test_major_raises_value_error(self):
        repeater = Dhis2Repeater.wrap({"dhis2_version": "2"})
        with self.assertRaises(ValueError):
            repeater.api_version

    def test_blank_raises_value_error(self):
        repeater = Dhis2Repeater.wrap({"dhis2_version": ""})
        with self.assertRaises(ValueError):
            repeater.api_version


class SlowApiVersionTest(TestCase):

    def setUp(self):
        self.repeater = Dhis2Repeater.wrap({
            "domain": "test-domain",
            "url": "https://dhis2.example.com/",
            "username": "admin",
            "password": "district",
        })

    def test_none_fetches_metadata(self):
        self.assertIsNone(self.repeater.dhis2_version)
        with patch('corehq.motech.dhis2.repeaters.fetch_metadata') as mock_fetch:
            mock_fetch.return_value = {"system": {"version": "2.31.6"}}
            self.assertEqual(self.repeater.api_version, 31)
            mock_fetch.assert_called()

    def test_max_version_exceeded_notifies_admins(self):
        major_ver, max_api_ver, patch_ver = LooseVersion(DHIS2_MAX_VERSION).version
        bigly_api_version = max_api_ver + 1
        bigly_dhis2_version = f"{major_ver}.{bigly_api_version}.{patch_ver}"
        with patch('corehq.motech.dhis2.repeaters.fetch_metadata') as mock_fetch, \
                patch('corehq.motech.dhis2.repeaters.get_requests') as mock_get_requests:
            mock_fetch.return_value = {"system": {"version": bigly_dhis2_version}}
            mock_requests = Mock()
            mock_get_requests.return_value = mock_requests

            self.assertEqual(self.repeater.api_version, bigly_api_version)
            mock_requests.notify_error.assert_called()
