from custom.enikshay.management.commands.utils import BaseEnikshayCaseMigration

from custom.enikshay.private_sector_datamigration.models import Beneficiary

DATAMIGRATION_CASE_PROPERTY = 'datamigration_district'


class Command(BaseEnikshayCaseMigration):
    case_type = 'person'
    case_properties_to_update = [
        'migration_created_case',
        'migration_comment',
        'legacy_districtId',
        'current_address_district_choice',
    ]
    datamigration_case_property = DATAMIGRATION_CASE_PROPERTY
    include_public_cases = False
    include_private_cases = True

    @staticmethod
    def get_case_property_updates(person, domain):
        if (
            person.get_case_property(DATAMIGRATION_CASE_PROPERTY) == 'yes'
            or person.get_case_property('migration_comment') not in [
                'july_7',
                'july_7_unassigned',
                'july_7-unassigned',
                'incr_bene_jul19',
            ]
            or not person.get_case_property('legacy_districtId')
            or person.get_case_property('current_address_district_choice')
        ):
            return {}
        else:
            beneficiary = Beneficiary.objects.get(caseId=person.get_case_property('migration_created_from_record'))
            if DISTRICT_ID_TO_LOCATION.get(beneficiary.districtId):
                return {
                    'current_address_district_choice': DISTRICT_ID_TO_LOCATION[beneficiary.districtId]
                }
        return {}

STATE_ID_TO_LOCATION = {
    '136': 'fa7472fe0c9751e5d14595c1a08698e2',
    '154': 'fa7472fe0c9751e5d14595c1a091f17d',
    '155': 'fa7472fe0c9751e5d14595c1a08c12b5',
    '2283': 'fa7472fe0c9751e5d14595c1a07b44b0',
    '2284': 'fa7472fe0c9751e5d14595c1a0858ee2',
    '2285': 'fa7472fe0c9751e5d14595c1a0749123', # typo?
    '2286': 'fa7472fe0c9751e5d14595c1a0833621',
    '2287': 'fa7472fe0c9751e5d14595c1a0844aab',
    '2288': 'fa7472fe0c9751e5d14595c1a07a5f13',
    '2289': 'fa7472fe0c9751e5d14595c1a0772ff2',
    '2294': 'fa7472fe0c9751e5d14595c1a07d7e61',
    '2298': 'fa7472fe0c9751e5d14595c1a0878be3',
    '2299': 'fa7472fe0c9751e5d14595c1a074036c',
    '2300': 'fa7472fe0c9751e5d14595c1a0818d00',
    '2301': 'fa7472fe0c9751e5d14595c1a07c6cd7',
    '2302': 'fa7472fe0c9751e5d14595c1a0856b69',
    '2303': 'fa7472fe0c9751e5d14595c1a07efcca',
    '2305': 'fa7472fe0c9751e5d14595c1a0846c7b',
    '2308': 'fa7472fe0c9751e5d14595c1a088b490',
    '2309': 'fa7472fe0c9751e5d14595c1a080b2ee',
    '2310': 'fa7472fe0c9751e5d14595c1a083567c',
    '2313': 'fa7472fe0c9751e5d14595c1a0793593',
}

DISTRICT_ID_TO_LOCATION = {
    '156': 'fa7472fe0c9751e5d14595c1a08f6416',
    '157': 'fa7472fe0c9751e5d14595c1a08bf499',
    '189': 'fa7472fe0c9751e5d14595c1a09001de',
    '598': 'fa7472fe0c9751e5d14595c1a0913ffe',
    '600': 'fa7472fe0c9751e5d14595c1a09132fd',
    '619': 'fa7472fe0c9751e5d14595c1a0903f30',
    '624': 'fa7472fe0c9751e5d14595c1a090156b',
    '625': 'fa7472fe0c9751e5d14595c1a08fc845',
    '626': 'fa7472fe0c9751e5d14595c1a08fc4b7',
    '632': 'fa7472fe0c9751e5d14595c1a08f8f29',
    '647': 'fa7472fe0c9751e5d14595c1a08eefcf',
    '1001': 'fa7472fe0c9751e5d14595c1a0868ef0',
    '1002': 'fa7472fe0c9751e5d14595c1a0868477',
    '1003': 'fa7472fe0c9751e5d14595c1a08679c8',
    '1004': 'fa7472fe0c9751e5d14595c1a086768c',
    '1005': 'fa7472fe0c9751e5d14595c1a086684c',
    '1006': 'fa7472fe0c9751e5d14595c1a0866118',
    '1007': 'fa7472fe0c9751e5d14595c1a0866076',
    '1008': 'fa7472fe0c9751e5d14595c1a0865b90',
    '1009': 'fa7472fe0c9751e5d14595c1a086568f',
    '1010': 'fa7472fe0c9751e5d14595c1a0864795',
    '1011': 'fa7472fe0c9751e5d14595c1a086445f',
    '1012': 'fa7472fe0c9751e5d14595c1a0863c55',
    '1013': 'fa7472fe0c9751e5d14595c1a08638a3',
    '1014': 'fa7472fe0c9751e5d14595c1a08634dc',
    '1015': 'fa7472fe0c9751e5d14595c1a08630dc',
    '1016': 'fa7472fe0c9751e5d14595c1a0862802',
    '1017': 'fa7472fe0c9751e5d14595c1a0861de5',
    '1018': 'fa7472fe0c9751e5d14595c1a0861524',
    '1019': 'fa7472fe0c9751e5d14595c1a0861086',
    '1020': 'fa7472fe0c9751e5d14595c1a0860337',
    '1021': 'fa7472fe0c9751e5d14595c1a085f684',
    '1022': 'fa7472fe0c9751e5d14595c1a0751a25',
    '1023': 'fa7472fe0c9751e5d14595c1a085e004',
    '1024': 'fa7472fe0c9751e5d14595c1a085d742',
    '1025': 'fa7472fe0c9751e5d14595c1a085d02a',
    '1026': 'fa7472fe0c9751e5d14595c1a085cdcb',
    '1027': 'fa7472fe0c9751e5d14595c1a085cdb0',
    '1028': 'fa7472fe0c9751e5d14595c1a085c4e9',
    '1029': 'fa7472fe0c9751e5d14595c1a085c41b',
    '1030': 'fa7472fe0c9751e5d14595c1a085c30b',
    '1031': 'fa7472fe0c9751e5d14595c1a085baa8',
    '1032': 'fa7472fe0c9751e5d14595c1a085b389',
    '1033': 'fa7472fe0c9751e5d14595c1a085b164',
    '1034': 'fa7472fe0c9751e5d14595c1a085a8e9',
    '1035': 'fa7472fe0c9751e5d14595c1a085a675',
    '1036': 'fa7472fe0c9751e5d14595c1a0859e8e',
    '1037': 'fa7472fe0c9751e5d14595c1a08598bf',
    '1038': 'fa7472fe0c9751e5d14595c1a08596e7',
    '1193': '',  # N/A
    '1194': '',  # N/A
    '1359': 'fa7472fe0c9751e5d14595c1a08b6cce',
    '1413': 'fa7472fe0c9751e5d14595c1a08aceb5',
    '1419': 'fa7472fe0c9751e5d14595c1a08ac7af',
    '1425': 'fa7472fe0c9751e5d14595c1a08ab1fb',
    '1428': 'fa7472fe0c9751e5d14595c1a08aa646',
    '2666': 'fa7472fe0c9751e5d14595c1a079a0cb',
}
