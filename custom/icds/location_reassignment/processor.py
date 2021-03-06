from django.db import transaction

from memoized import memoized

from corehq.apps.locations.models import LocationType, SQLLocation
from custom.icds.location_reassignment.const import SPLIT_OPERATION
from custom.icds.location_reassignment.exceptions import (
    InvalidTransitionError,
    LocationCreateError,
)
from custom.icds.location_reassignment.utils import (
    deprecate_locations,
    get_supervisor_id,
)


class Processor(object):
    def __init__(self, domain, transitions, new_location_details, user_transitions, site_codes):
        """
        :param domain: domain
        :param transitions: transitions in format generated by Parser
        :param new_location_details: details necessary to create new locations
        :param site_codes: site codes of all locations undergoing transitions
        """
        self.domain = domain
        self.location_types_by_code = {lt.code: lt for lt in LocationType.objects.by_domain(self.domain)}
        self.transitions = transitions
        self.new_location_details = new_location_details
        self.user_transitions = user_transitions
        self.site_codes = site_codes
        self.transiting_locations_by_site_code = {
            loc.site_code: loc
            for loc in SQLLocation.active_objects.filter(domain=self.domain, site_code__in=self.site_codes)
        }

    def process(self):
        self._create_new_locations()
        # process each sheet, in reverse order of hierarchy
        for location_type_code in list(reversed(list(self.location_types_by_code))):
            for operation, transitions in self.transitions[location_type_code].items():
                self._perform_transitions(operation, transitions)
        self.update_users()

    def _create_new_locations(self):
        parent_locations_by_site_code = self._get_existing_parent_locations()

        with transaction.atomic():
            for location_type_code in self.location_types_by_code:
                new_locations_details = self.new_location_details.get(location_type_code, {})
                for site_code, details in new_locations_details.items():
                    # if location already present don't try creating it
                    if site_code in self.transiting_locations_by_site_code:
                        continue
                    parent_location = None
                    if details['parent_site_code']:
                        parent_location = parent_locations_by_site_code[details['parent_site_code']]
                    location = SQLLocation.objects.create(
                        domain=self.domain, site_code=site_code, name=details['name'],
                        parent=parent_location,
                        location_type=self.location_types_by_code[location_type_code],
                        metadata={'lgd_code': details['lgd_code']}
                    )
                    # add new location in case its a parent to any other locations getting created
                    parent_locations_by_site_code[site_code] = location
                    # update transiting locations mapping
                    self.transiting_locations_by_site_code[site_code] = location

    def _get_existing_parent_locations(self):
        existing_parent_site_codes = set()

        for location_type_code in list(reversed(list(self.location_types_by_code))):
            new_locations_details = self.new_location_details.get(location_type_code, {})
            for site_code, details in new_locations_details.items():
                if details['parent_site_code']:
                    existing_parent_site_codes.add(details['parent_site_code'])
                # remove it from parent site codes if it itself needs to be created
                existing_parent_site_codes.discard(site_code)

        if existing_parent_site_codes:
            return self._get_locations_by_site_codes(existing_parent_site_codes)
        return {}

    def _get_locations_by_site_codes(self, site_codes):
        parents = SQLLocation.active_objects.filter(domain=self.domain, site_code__in=site_codes)
        if len(parents) != len(site_codes):
            missing_site_codes = site_codes - set([loc.site_code for loc in parents])
            raise LocationCreateError(
                "Could not find parent locations with following site codes %s" % ",".join(missing_site_codes))
        return {
            loc.site_code: loc for loc in parents
        }

    def _perform_transitions(self, operation, transitions):
        # split operation has the old site code as the key whereas others have the new site code
        for from_site_codes, to_site_codes in transitions.items():
            if operation == SPLIT_OPERATION:
                old_site_codes, new_site_codes = from_site_codes, to_site_codes
            else:
                new_site_codes, old_site_codes = from_site_codes, to_site_codes
            errors = deprecate_locations(self.domain, self._get_locations(old_site_codes),
                                         self._get_locations(new_site_codes), operation)
            if errors:
                raise InvalidTransitionError(",".join(errors))

    def _get_locations(self, site_codes):
        site_codes = site_codes if isinstance(site_codes, list) else [site_codes]
        locations = [self.transiting_locations_by_site_code.get(site_code)
                     for site_code in site_codes
                     if self.transiting_locations_by_site_code.get(site_code)]
        if len(locations) != len(site_codes):
            loaded_site_codes = [loc.site_code for loc in locations]
            missing_site_codes = set(site_codes) - set(loaded_site_codes)
            raise InvalidTransitionError(
                "Could not load location with following site codes: %s" % ",".join(missing_site_codes))
        return locations

    def update_users(self):
        from custom.icds.location_reassignment.tasks import update_usercase
        for old_username, new_username in self.user_transitions.items():
            update_usercase.delay(self.domain, old_username, new_username)


class HouseholdReassignmentProcessor():
    def __init__(self, domain, reassignments):
        self.domain = domain
        self.reassignments = reassignments

    def process(self):
        from custom.icds.location_reassignment.utils import reassign_household_case
        old_site_codes = set()
        new_site_codes = set()
        for household_id, details in self.reassignments.items():
            old_site_codes.add(details['old_site_code'])
            new_site_codes.add(details['new_site_code'])
        old_locations_by_site_code = {
            loc.site_code: loc
            for loc in SQLLocation.active_objects.filter(domain=self.domain, site_code__in=old_site_codes)}
        new_locations_by_site_code = {
            loc.site_code: loc
            for loc in SQLLocation.active_objects.filter(domain=self.domain, site_code__in=new_site_codes)}
        for household_id, details in self.reassignments.items():
            old_owner_id = old_locations_by_site_code[details['old_site_code']].location_id
            new_owner_id = new_locations_by_site_code[details['new_site_code']].location_id
            supervisor_id = self._supervisor_id(old_owner_id)
            reassign_household_case(self.domain, household_id, old_owner_id, new_owner_id, supervisor_id)

    @memoized
    def _supervisor_id(self, location_id):
        return get_supervisor_id(self.domain, location_id)
