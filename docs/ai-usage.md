# How AI was used

Tool: Claude (chat). The assessment brief was given to it as screenshots, and the work was done in a series of
steps, each ending in a commit.

## Process
1. **Requirements first.** Asked for a one-page requirements doc before any code: goal, scope, deliberate exclusions with reasons
   (`docs/requirements.md`).
2. **Foundation before features.** Schema, currency model and validation were written and unit-tested before any endpoints.
3. **Tests alongside each layer**, then run immediately. The AI proposed behaviour; the tests pinned it down.
4. **Measure, don't assume.** Seeded 10,000 rows and benchmarked every endpoint rather than asserting it was fast.
5. **UI last**, against the already-tested API.

## Prompts / instructions given (summary)
- "Build employee salary management software for an org of 10,000 employees; HR manager persona; manage salary data and
  answer questions about how the org pays people." (the assessment brief, verbatim as screenshots)
- Constraints supplied: backend + UI, relational DB (SQLite), seed script with 10,000 employees, unit tests that are fast,
  deterministic and easy to understand, incremental commits, one-page requirements doc, deployable.
- Direction on engineering judgement: prefer the simplest design that is correct; call out what is excluded and why.

## Where human review mattered (decisions and corrections)
- **Currency model**: multi-country salaries can't be averaged raw. Chose local-currency storage + USD normalisation at read time.
- **A bug the tests caught**: stripping `%`/`_` from search input made `q=%` match everyone and broke searching `john_doe`.
  Fixed with proper `LIKE … ESCAPE` and regression tests.
- **Sorting by salary** uses USD, otherwise INR/JPY values would always rank first.
- **Scope cuts**: auth, bonuses/equity, gender pay-gap analysis, live FX — each deliberately excluded (see requirements).

## Honest limitations
- The UI could not be exercised in a real browser in the authoring environment: JS modules are syntax-checked and every file is
  served correctly, but click-through testing should be done before submitting (see README checklist).
- Deployment and the demo video must be done by the submitter.

> Edit this file to reflect your own actual prompts and review notes — it should be an accurate account of *your* process.
