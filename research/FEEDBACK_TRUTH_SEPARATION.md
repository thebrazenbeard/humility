# Separate scoring truth from simulated learner feedback

Research-only contract; this is not a Vera Mono runtime component or an
independent evaluator.

`evaluate_stream(cases, *, feedback_overrides=None)` preserves the original
four-field case tuples and default behavior. `cases` is the frozen evaluator
truth sequence. `feedback_overrides` is an optional dict keyed by existing case
ID. The override values are deliberately **untrusted training feedback**,
not corrected truth, independent corroboration, or evidence of source quality.

All keys and value types are rejected before launching a child. Each prediction
is returned and scored against the original case outcome before the chosen
feedback value is passed to the child for updating the NEXT prediction. Every
case retains exactly one feedback event. Receipts carry the number of supplied
overrides and of feedback values diverging from scoring truth. Source tags
`EVALUATOR_LOCAL_UNAUTHENTICATED` and `SIMULATED_UNTRUSTED` describe the
claimed roles in the local experiment, not identity/authenticity attestations.

Compare matching case IDs and identical sequence/budgets under clean and
poisoned feedback, as well as no-learning/frozen and shuffled feedback controls.
Retain phase-specific negative transfer and unchanged predictions before each
feedback event. Do not count an identical numerical override as another
independent source or let the learner self-certify evaluator outcomes.

Security/qualification limits: the subprocess and evaluator share filesystem
and host authority; the generator, truth labels and feedback may be under a
single author's control. No source-group authentication, hidden evaluator
process isolation, executable method/callable closure witness, generalization
outside toy source, cold canonical restart, calibration across real uncertainty
types, autonomous learning or production authority follows. Epistemic humility
remains a required evidence-sensitive norm, not an automatically passed test.

The four-lane review discussion is maintained privately in the Chat
Communication Bus issue #387. Evidence must be bound to frozen exact heads.
