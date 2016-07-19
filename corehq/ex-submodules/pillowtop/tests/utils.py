import sys
from select import select

from django.conf import settings
from elasticsearch import TransportError

from pillowtop.es_utils import ElasticsearchIndexInfo
from pillowtop.listener import AliasedElasticPillow

TEST_ES_META = {"settings":
    {
        "analysis": {
            "analyzer": {
                "default": {
                    "type": "custom",
                    "tokenizer": "whitespace",
                    "filter": ["lowercase"]
                },
            }
        }
    }
}

TEST_ES_MAPPING = {
    '_meta':
        {
            'comment': 'You know, for tests',
            'created': '2015-10-07 @czue'
        },
    "properties": {
        "doc_type": {
            "index": "not_analyzed", "type": "string"
        },
    }
}

TEST_ES_TYPE = 'test_doc'
TEST_ES_INDEX = 'test_pillowtop_index'
TEST_ES_ALIAS = 'pillowtop_tests'
TEST_INDEX_INFO = ElasticsearchIndexInfo(
    index=TEST_ES_INDEX,
    alias=TEST_ES_ALIAS,
    type=TEST_ES_TYPE,
    meta=TEST_ES_META,
    mapping=TEST_ES_MAPPING
)


def get_doc_count(es, index, refresh_first=True):
    if refresh_first:
        # we default to calling refresh since ES might have stale data
        es.indices.refresh(index)
    stats = es.indices.stats(index)
    return stats['indices'][index]['total']['docs']['count']


def get_index_mapping(es, index, doc_type):
    def _format_mapping_for_es_version(mapping):
        if settings.ELASTICSEARCH_VERSION < 1.0:
            return mapping[doc_type]
        else:
            return mapping[index]['mappings'][doc_type]
    try:
        return _format_mapping_for_es_version(es.indices.get_mapping(index, doc_type))
    except TransportError:
        return {}


def timed_raw_input(prompt, timeout=None, default="", stdout=sys.stdout):
    # http://stackoverflow.com/a/3471853/10840
    # does not work on Windows
    timeout_arg = () if timeout is None else (timeout,)
    stdout.write(prompt)
    rlist, _, _ = select([sys.stdin], [], [], *timeout_arg)
    if rlist:
        return sys.stdin.readline()
    return default
