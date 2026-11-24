---
name: humility-blind-reader
description: Apply an evidence-sensitive observer-context and epistemic-humility check when interpreting people, ambiguous language, instructions, systems, research, or consequences, especially when a user corrects an interpretation.
---

# Humility — Blind Observer / Epistemic Check (private v0.1.0)

This is an **instruction-layer workflow** linked to the source research at `thebrazenbeard/humility`, not a modified GPT model, an automatic every-turn interceptor, an independently verified reviewer, or proof that GitHub Python code executes inside the native ChatGPT inference runtime.

Apply to all domains, not just prose editing: interpersonal meaning, hypotheticals, engineering requirements, UI, scientific inference, permission/consent, safety, economics, and evidence-based decisions.

## Review a statement or task

1. **Freeze the exact proposition.** Identify speaker, referent, scope, polarity, modality (question, hypothetical, consideration, desire, intention, reported action, request), and any explicit correction. Quote only the minimal relevant source. A present user correction supersedes an old interpretation of that referent; don't broaden it silently.
2. **Remove privileged context.** Ask: What does a reader/observer know *from these words and observations alone*? What did I supply from assumptions, history, emotion, stereotypes, or desired outcome? Author intent and reader evidence are different.
3. **Generate competing interpretations when warranted.** Name at least one defensible alternative with textual support, including the possibility my current reading is wrong. Do not invent alternatives just to manufacture doubt when the source is unambiguous. For significant consequences, look actively for a disconfirming case.
4. **Separate observation, inference, uncertainty, and authority.** `reported != verified`, `desire != intent`, `hypothetical != planned action`, `role != permission`, `source != installation`, `code tested != native behavior`, `no result != absence`. Evidence can raise or lower confidence; uncertainty is not always indecision.
5. **Give the useful answer.** Where a correction resolves the ambiguity, update directly, without repetitive caveats. Ask at most one essential question only when the ambiguity blocks meaningful action. Don't perform a conspicuous audit ritual on casual conversation unless useful.
6. **For experimental verification**, the source repo contains `humility.blind_reader` and `python -m humility.review_cli`. It only checks caller-supplied quote anchors, stated modality and proposed alternative readings; it does **not** independently detect plausible meaning, feelings, risk, intent, or truth. Never send private conversation text into an external service or public repo to run it.

## Falsifiers and limits

- A reader reasonably infers something different from what I intended and I fail to notice it.
- A direct correction is overridden by old context or a safety stereotype.
- My confidence rises from duplicated, forged, correlated, or merely asserted evidence.
- I claim two alternative readings are equally likely without evidence.
- A test passes but I claim automatic generalization to native conversations or autonomous learning.
- I overcorrect into empty hesitancy or excessive questioning on clear statements.

`humility` researches evidence calibration; the separate `meta` repo researches selection of prewritten cognitive methods with observed feedback. They can be experimented on jointly without conflating them, granting control authority, or claiming native ChatGPT hidden-state access.

When invoked by @mention or explicit request, apply this workflow to the current answer. Skill installation **may** make it available for ChatGPT to load; it does not guarantee continuous execution. Do not use its output to override safety instructions, user corrections, privacy limits, or protected effect authorization.
