# Humility Blind Reader / Observer-Context Contract V1

Purpose: test *how the same observation could be reasonably read by someone without the author's privileged context* across conversation, systems, research, images, interfaces, decisions, and fiction.

## Bounded executable seam

- `humility.blind_reader.CandidateReading` records caller-authored interpretations, verbatim source anchors, speech-act/modality labels, and explicit unstated assumptions.
- `review(utterance, declared_modality, candidates)` validates types, deduplicates candidate identities, rejects source quotes absent from the visible utterance, and flags different readings, assumptions, and changes of modality.
- `python -m humility.review_cli` consumes one bounded, <=16 KiB UTF-8 JSON object with schema `HUMILITY_BLIND_READER_V1`, outputs a stateless JSON result, performs no network action and persists nothing.
- `REVIEW_REQUIRED` means some alternatives, assumptions or mismatches were *submitted* for human/model review. It is NOT a verdict that each interpretation is plausible or that ambiguity has been proven.
- `NO_CONFLICT_OBSERVED` is likewise NOT a conclusion of correctness, completeness or truth.
- Both the declared modality and readings are caller-supplied conjectures. The software does NOT classify natural language, infer intent, feelings or consent, authenticate evidence, or verify reality.
- Every result has `unverified_plausibility=true` and `action_effect=NONE`.

## Example input

```json
{
  "schema":"HUMILITY_BLIND_READER_V1",
  "utterance":"The bag was over the sleeping child's head.",
  "declared_modality":"DESCRIPTION",
  "readings":[
    {"reading_id":"shade", "paraphrase":"Bag suspended as rain shield", "quoted_evidence":["bag was over"], "modality":"DESCRIPTION", "unstated_assumptions":["bag is held above rather than enclosing the face"]},
    {"reading_id":"danger", "paraphrase":"Bag enclosing the face", "quoted_evidence":["bag was over"], "modality":"DESCRIPTION", "unstated_assumptions":["bag touches the face"]}
  ]
}
```

## Negative controls

1. **Modality escalation:** a hypothetical or abstract consideration must not silently become an intention or prepared action; report a modality mismatch, not a fact about the speaker.
2. **Forged quotation:** candidate evidence missing from the available utterance must be rejected.
3. **Alternative invention:** two invented readings alone don't prove plausibility, ambiguity or correctness; evaluation remains external.
4. **Correction precedence:** the latest direct correction supersedes a stale interpretation of the same referent; the host must supply corrected current context. This routine cannot authenticate correction provenance.
5. **Authority:** review grants no consent, action, permission, publication, diagnosis, or release authority.

Run the focused tests: `python -m unittest discover -s tests -p 'test_blind_reader*.py' -v`.

Source presence, unit tests, plugin package, installation, actual invocation, and improvement of native ChatGPT behavior are distinct states.
