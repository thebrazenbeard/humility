"""Bounded, offline, stateless JSON interface for caller-authored blind-read audits.

No automatic text understanding, network, persistence, or action authority.
"""
from dataclasses import asdict
import json
import sys
from humility.blind_reader import CandidateReading, review

SCHEMA = 'HUMILITY_BLIND_READER_V1'
_MAX_BYTES = 16384
_FIELDS = {'schema', 'utterance', 'declared_modality', 'readings'}
_READING_FIELDS = {'reading_id', 'paraphrase', 'quoted_evidence', 'modality',
                   'unstated_assumptions'}


def _pairs(items):
    obj = {}
    for key, value in items:
        if key in obj:
            raise ValueError('duplicate JSON key')
        obj[key] = value
    return obj


def _exact_object(x, required, allowed):
    if type(x) is not dict or not required <= set(x) or not set(x) <= allowed:
        raise ValueError('invalid object fields')


def _load(payload: bytes):
    if len(payload) > _MAX_BYTES:
        raise ValueError('payload too large')
    doc = json.loads(payload.decode('utf-8'), object_pairs_hook=_pairs)
    _exact_object(doc, _FIELDS, _FIELDS)
    if doc['schema'] != SCHEMA or type(doc['readings']) is not list:
        raise ValueError('invalid schema or readings')
    readings = []
    for entry in doc['readings']:
        _exact_object(entry, _READING_FIELDS - {'unstated_assumptions'}, _READING_FIELDS)
        readings.append(CandidateReading(entry['reading_id'], entry['paraphrase'],
            entry['quoted_evidence'], entry['modality'], entry.get('unstated_assumptions', ())))
    return review(doc['utterance'], doc['declared_modality'], readings)


def main():
    try:
        # Read one byte past maximum so oversized records can be rejected.
        outcome = _load(sys.stdin.buffer.read(_MAX_BYTES + 1))
        print(json.dumps({'schema': 'HUMILITY_BLIND_READER_RESULT_V1', **asdict(outcome)}, sort_keys=True))
        return 0
    except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
        # Never echo potentially private/untrusted input.
        print(json.dumps({'schema': 'HUMILITY_BLIND_READER_RESULT_V1', 'status': 'ERROR',
                          'action_effect': 'NONE'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
