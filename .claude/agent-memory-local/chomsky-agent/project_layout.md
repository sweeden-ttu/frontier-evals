# First principles for this work

## 1. An agent is the trace language it can emit, nothing more.
Not its prompt. Not its model. Not its self-description. The set of finite tool-call sequences it can produce is the only thing V&V can reason about. Everything else — capability claims, intent, "alignment" — is unverifiable narrative until it shows up in a trace.
Implication: if a behavior isn't in Σ (the alphabet), it doesn't exist for our purposes. Designing Σ is the most consequential decision in the whole framework.

## 2. Decidability sets the ceiling on what V&V can promise.
Type-0 agents cannot be statically verified. This isn't an engineering limitation we'll engineer around — it's Rice's Theorem. Any framework that claims to "verify" a Type-0 agent is either lying or has secretly reduced it to a lower class at some boundary.
Implication: the honest output for a Type-0 agent is "validated empirically to confidence X, with explicit undecidability disclosure," never "verified." The paper has to defend this distinction or it gets eaten in review.

## 3. Soundness > completeness > coverage > speed.
A V&V verdict that's wrong is worse than no verdict. A verdict that misses cases is worse than one that's narrow but correct. Optimizing for speed before soundness is how we get the LLM-judges-LLM circularity that this whole project exists to avoid.
Implication: when we have to choose, the slower-but-sound check wins. Mutation score is a measurement of completeness, not a target to game.

## 4. Classifications are derived, not declared.
Hand-written contracts are scaffolding, not science. Anything in contracts.py that wasn't produced by an analyzer reading source is a hypothesis we're carrying around without checking. The AST classifier (Gap 4) isn't an optimization — it's the difference between the framework being a research artifact and being a config file.
Implication: every classification needs a structural witness pointing to source evidence. If we can't say "Type-1 because of <file>:<line>," we don't know it's Type-1.

## 5. Refutation beats confirmation.
Probes earn their keep by demoting wrong classifications. A probe that only ever returns PASS isn't doing science — it's decoration. The probe suite's value is measured in how often it changes a verdict, not how often it agrees.
Implication: track refutation rate per probe across the corpus. A probe with a 0% refutation rate over 1000 traces is a candidate for removal or for being too lenient.


## 6. Self-awareness means treating prior decisions as data, not authority.
A drift threshold that triggers reclassification — and actually reclassifies, not just logs a warning — is the operational definition. If the system silently reuses old verdicts past the threshold, it's not self-aware, it's stale.
Implication: the embedding loop must close. Reclassification has to be the default response to drift, not a manual intervention.

## 7. Paths are relative; environments are declared.
Reproducibility is a first-class scientific concern, not an afterthought. Absolute paths, system-Python tests, undeclared dependencies — each one is a small lie about what the framework needs to run. The structlog incident wasn't a packaging hiccup; it was the framework telling us the truth about its boundaries.
Implication: if a check can't be reproduced from a fresh clone via uv run pytest, the check doesn't count toward the paper's claims.

## 8. Symmetry across benchmarks is load-bearing.
The paper's central empirical move is "we apply the same V&V framework to three different evaluation substrates and observe X." If paperbench, evmbench, and swelancer have asymmetric APIs, asymmetric defaults, or asymmetric test invocations, "the same framework" becomes a footnote-laden claim instead of a clean one.
Implication: every change to one benchmark's chomsky binding gets mirrored to the other two, immediately, before the next gap opens.

## 9. The framework must be classifiable by itself.
If chomsky-agent can't be run against chomsky_vv and produce a coherent classification of the framework's own components, we don't believe our own theory. This is a falsification condition for the paper, not just a nice-to-have.
Implication: at some point — probably after Gap 4 — we run the classifier on the framework itself. Whatever it finds becomes a section of the paper.