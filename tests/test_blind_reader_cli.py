import json
import subprocess
import sys
import unittest


class BlindReaderCLITests(unittest.TestCase):
    def invoke(self, payload):
        data = payload if isinstance(payload, str) else json.dumps(payload)
        proc = subprocess.run([sys.executable, '-m', 'humility.review_cli'],
                              input=data, text=True, capture_output=True, timeout=10)
        return proc, json.loads(proc.stdout)

    def test_valid_frame_returns_bounded_review_not_a_verdict(self):
        p = {'schema': 'HUMILITY_BLIND_READER_V1', 'utterance': 'a bag above the head',
             'declared_modality': 'DESCRIPTION', 'readings': [
                {'reading_id': 'shelter', 'paraphrase': 'shield from rain',
                 'quoted_evidence': ['bag above the head'], 'modality': 'DESCRIPTION'},
                {'reading_id': 'threat', 'paraphrase': 'covers face',
                 'quoted_evidence': ['bag above the head'], 'modality': 'DESCRIPTION'}]}
        proc, out = self.invoke(p)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(out['status'], 'REVIEW_REQUIRED')
        self.assertEqual(out['unverified_plausibility'], True)
        self.assertEqual(out['action_effect'], 'NONE')

    def test_extra_keys_or_duplicate_keys_refused(self):
        p = {'schema': 'HUMILITY_BLIND_READER_V1', 'utterance': 'x',
             'declared_modality': 'ASSERTION', 'readings': [{'reading_id': 'a',
             'paraphrase': 'x', 'quoted_evidence': ['x'], 'modality': 'ASSERTION'}],
             'action': 'DELETE'}
        proc, out = self.invoke(p)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(out['status'], 'ERROR')
        proc, out = self.invoke('{"schema":"HUMILITY_BLIND_READER_V1","schema":"X"}')
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(out['status'], 'ERROR')

    def test_rejects_large_payload_without_echo(self):
        proc, out = self.invoke('secret here' * 2000)
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn('secret', proc.stdout)
        self.assertEqual(out['status'], 'ERROR')

if __name__ == '__main__': unittest.main()
