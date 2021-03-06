from datetime import datetime

from django.test import TestCase

from corehq.apps.commtrack.tests.util import bootstrap_domain
from corehq.apps.locations.tests.util import setup_locations_and_types
from custom.icds.location_reassignment.const import (
    DEPRECATED_AT,
    DEPRECATED_TO,
    DEPRECATED_VIA,
    DEPRECATES,
    DEPRECATES_AT,
    DEPRECATES_VIA,
)
from custom.icds.location_reassignment.models import (
    ExtractOperation,
    MergeOperation,
    MoveOperation,
    SplitOperation,
)


class TestOperation(TestCase):
    operation = None
    domain = "test"
    location_type_names = ['state', 'county', 'city']
    location_structure = [
        ('Massachusetts', [
            ('Middlesex', [
                ('Cambridge', []),
                ('Somerville', []),
            ]),
            ('Suffolk', [
                ('Boston', []),
            ])
        ]),
        ('California', [
            ('Los Angeles', []),
        ])
    ]

    @classmethod
    def setUpClass(cls):
        super(TestOperation, cls).setUpClass()
        cls.domain_obj = bootstrap_domain(cls.domain)

    def setUp(self):
        super(TestOperation, self).setUp()
        self.location_types, self.locations = setup_locations_and_types(
            self.domain,
            self.location_type_names,
            [],
            self.location_structure,
        )

    def check_operation(self, old_locations, new_locations, archived=True):
        self.operation(self.domain, old_locations, new_locations).perform()
        old_location_ids = [loc.location_id for loc in old_locations]
        new_location_ids = [loc.location_id for loc in new_locations]
        operation_time = old_locations[0].metadata[DEPRECATED_AT]
        self.assertIsInstance(operation_time, datetime)
        for old_location in old_locations:
            self.assertEqual(old_location.metadata[DEPRECATED_TO], new_location_ids)
            self.assertEqual(old_location.metadata[DEPRECATED_VIA], self.operation.type)
            self.assertEqual(old_location.metadata[DEPRECATED_AT], operation_time)
            if archived:
                self.assertTrue(old_location.is_archived)
        for new_location in new_locations:
            self.assertEqual(new_location.metadata[DEPRECATES], old_location_ids)
            self.assertEqual(new_location.metadata[DEPRECATES_VIA], self.operation.type)
            self.assertEqual(new_location.metadata[DEPRECATES_AT], operation_time)


class TestMergeOperation(TestOperation):
    operation = MergeOperation

    def test_perform(self):
        new_locations = [self.locations['Boston']]
        old_locations = [self.locations['Cambridge'], self.locations['Somerville']]
        self.check_operation(old_locations, new_locations)


class TestSplitOperation(TestOperation):
    operation = SplitOperation

    def test_perform(self):
        old_locations = [self.locations['Boston']]
        new_locations = [self.locations['Cambridge'], self.locations['Somerville']]
        self.check_operation(old_locations, new_locations)


class TestExtractOperation(TestOperation):
    operation = ExtractOperation

    def test_perform(self):
        old_locations = [self.locations['Boston']]
        new_locations = [self.locations['Cambridge']]
        self.check_operation(old_locations, new_locations, archived=False)


class TestMoveOperation(TestOperation):
    operation = MoveOperation

    def test_perform(self):
        old_locations = [self.locations['Boston']]
        new_locations = [self.locations['Cambridge']]
        self.check_operation(old_locations, new_locations)
