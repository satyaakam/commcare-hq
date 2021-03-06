from collections import defaultdict

from corehq.apps.locations.models import LocationType, SQLLocation
from custom.icds.location_reassignment.const import (
    AWC_CODE_COLUMN,
    CURRENT_SITE_CODE_COLUMN,
    EXTRACT_OPERATION,
    HOUSEHOLD_ID_COLUMN,
    MERGE_OPERATION,
    MOVE_OPERATION,
    NEW_LGD_CODE,
    NEW_NAME,
    NEW_PARENT_SITE_CODE,
    NEW_SITE_CODE_COLUMN,
    NEW_USERNAME_COLUMN,
    OPERATION_COLUMN,
    SPLIT_OPERATION,
    USERNAME_COLUMN,
    VALID_OPERATIONS,
)


class Parser(object):
    def __init__(self, domain, workbook):
        """
        Receives a worksheet generated by custom.icds.location_reassignment.download.Download
        and generates an output like
        {
            location_type_code:
                'Merge': {
                    'New location site code': ['Old location site code', 'Old location site code']
                },
                'Split': {
                    'Old location site code': ['New location site code', 'New location site code']
                },
                'Rename': {
                    'New location site code': 'Old location site code'
                },
                'Extract': {
                    'New location site code': 'Old location site code'
                }
        }
        """
        self.domain = domain
        self.workbook = workbook
        # mapping each location code to the type of operation requested for it
        self.requested_transitions = {}
        self.site_codes_to_be_archived = []
        self.location_type_codes = list(map(lambda lt: lt.code, LocationType.objects.by_domain(self.domain)))
        self.new_location_details = {location_type_code: {} for location_type_code in self.location_type_codes}
        self.user_transitions = {}
        self.valid_transitions = {location_type_code: {
            MERGE_OPERATION: defaultdict(list),
            SPLIT_OPERATION: defaultdict(list),
            MOVE_OPERATION: {},
            EXTRACT_OPERATION: {},
        } for location_type_code in self.location_type_codes}
        self.errors = []

    def parse(self):
        for worksheet in self.workbook.worksheets:
            location_type_code = worksheet.title
            for row in worksheet:
                operation = row.get(OPERATION_COLUMN)
                if not operation:
                    continue
                if operation not in VALID_OPERATIONS:
                    self.errors.append("Invalid Operation %s" % operation)
                    continue
                self._parse_row(row, location_type_code)
        self.validate()
        return self.errors

    def _parse_row(self, row, location_type_code):
        operation = row.get(OPERATION_COLUMN)
        old_site_code = row.get(CURRENT_SITE_CODE_COLUMN)
        new_site_code = row.get(NEW_SITE_CODE_COLUMN)
        if not old_site_code or not new_site_code:
            self.errors.append("Missing location code for %s, got old: '%s' and new: '%s'" % (
                operation, old_site_code, new_site_code
            ))
            return
        if old_site_code == new_site_code:
            self.errors.append("No change in location code for %s, got old: '%s' and new: '%s'" % (
                operation, old_site_code, new_site_code
            ))
            return
        if bool(row.get(NEW_USERNAME_COLUMN)) != bool(row.get(USERNAME_COLUMN)):
            self.errors.append("Need both old and new username for %s operation on location '%s'" % (
                operation, old_site_code
            ))
            return
        if self._invalid_row(operation, old_site_code, new_site_code):
            return
        self._note_transition(operation, location_type_code, new_site_code, old_site_code)
        if new_site_code in self.new_location_details[location_type_code]:
            details = self.new_location_details[location_type_code][new_site_code]
            if (details['name'] != row.get(NEW_NAME)
                    or details['parent_site_code'] != row.get(NEW_PARENT_SITE_CODE)
                    or details['lgd_code'] != row.get(NEW_LGD_CODE)):
                self.errors.append("New location %s reused with different information" % new_site_code)
        else:
            self.new_location_details[location_type_code][new_site_code] = {
                'name': row.get(NEW_NAME),
                'parent_site_code': row.get(NEW_PARENT_SITE_CODE),
                'lgd_code': row.get(NEW_LGD_CODE)
            }
        if row.get(NEW_USERNAME_COLUMN) and row.get(USERNAME_COLUMN):
            self.user_transitions[row.get(NEW_USERNAME_COLUMN)] = row.get(USERNAME_COLUMN)

    def _invalid_row(self, operation, old_site_code, new_site_code):
        invalid = False
        if old_site_code in self.requested_transitions:
            if self.requested_transitions.get(old_site_code) != operation:
                self.errors.append("Multiple transitions for %s, %s and %s" % (
                    old_site_code, self.requested_transitions.get(old_site_code), operation))
                invalid = True
        if new_site_code in self.requested_transitions:
            if self.requested_transitions.get(new_site_code) != operation:
                self.errors.append("Multiple transitions for %s, %s and %s" % (
                    new_site_code, self.requested_transitions.get(new_site_code), operation))
                invalid = True
        return invalid

    def _note_transition(self, operation, location_type_code, new_site_code, old_site_code):
        if operation == MERGE_OPERATION:
            self.valid_transitions[location_type_code][operation][new_site_code].append(old_site_code)
        elif operation == SPLIT_OPERATION:
            self.valid_transitions[location_type_code][operation][old_site_code].append(new_site_code)
        elif operation == MOVE_OPERATION:
            self.valid_transitions[location_type_code][operation][new_site_code] = old_site_code
        elif operation == EXTRACT_OPERATION:
            self.valid_transitions[location_type_code][operation][new_site_code] = old_site_code
        self.site_codes_to_be_archived.append(old_site_code)
        self.requested_transitions[old_site_code] = operation
        self.requested_transitions[new_site_code] = operation

    def validate(self):
        if self.site_codes_to_be_archived:
            self._validate_descendants_archived()

    def _validate_descendants_archived(self):
        """
        ensure all locations getting archived, also have their descendants getting archived
        """
        site_codes_to_be_archived = set(self.site_codes_to_be_archived)
        locations_to_be_archived = SQLLocation.active_objects.filter(site_code__in=self.site_codes_to_be_archived)
        for location in locations_to_be_archived:
            descendants_sites_codes = (location.get_descendants().filter(is_archived=False).
                                       values_list('site_code', flat=True))
            missing_site_codes = set(descendants_sites_codes) - site_codes_to_be_archived
            if missing_site_codes:
                self.errors.append("Location %s is getting archived but the following descendants are not %s" % (
                    location.site_code, ",".join(missing_site_codes)
                ))


class HouseholdReassignmentParser(object):
    def __init__(self, domain, workbook):
        self.domain = domain
        self.workbook = workbook
        self.reassignments = {}  # household id mapped to a dict with old_site_code and new_site_code

    def parse(self):
        errors = []
        site_codes = set()
        for worksheet in self.workbook.worksheets:
            location_site_code = worksheet.title
            site_codes.add(location_site_code)
            for row in worksheet:
                household_id = row.get(HOUSEHOLD_ID_COLUMN)
                new_awc_code = row.get(AWC_CODE_COLUMN)
                if not household_id:
                    errors.append("Missing Household ID for %s" % location_site_code)
                    continue
                if not new_awc_code:
                    errors.append("Missing New AWC Code for household ID %s" % household_id)
                    continue
                site_codes.add(new_awc_code)
                self.reassignments[household_id] = {
                    'old_site_code': location_site_code,
                    'new_site_code': new_awc_code
                }
        locations = SQLLocation.active_objects.filter(domain=self.domain, site_code__in=site_codes)
        if len(locations) != len(site_codes):
            site_codes_found = set([l.site_code for l in locations])
            errors.append(
                "Missing site codes %s" % ",".join(site_codes - site_codes_found)
            )
        return errors
