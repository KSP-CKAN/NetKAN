---
name: netkan-pr-review
description: Reviews a KSP-CKAN/NetKAN pull request that adds a new mod and reports whether the netkan is correct or which corrections it needs. Use when asked to review, check, vet, or look at a NetKAN PR, a netkan file, or a new mod submission by PR number. Read-only, never edits the PR.
---

# Review a NetKAN PR

Review one PR to `KSP-CKAN/NetKAN` as a CKAN metadata wrangler. Produce a report;
do not edit the submission, push, post comments, or merge. The diagnostic script
may write local evidence files and download tools.

The usual input is a PR number or URL for a new mod. For a PR that changes an
existing netkan, review the resulting file as a new submission and ignore its
CKAN-meta history.

## Maintaining this skill

Keep each kind of instruction in its own place:

| To change... | Edit... |
| --- | --- |
| How to gather evidence and conduct the review | This file, steps 1-4 |
| What makes a submission correct, including exceptions | [Review rules](reference/review-rules.md) |
| Severity, verdict selection, or report layout | This file, step 5 |
| Field syntax and allowed values | [Spec cheatsheet](reference/spec-cheatsheet.md) |
| Historical examples and reviewer feedback | [Common fixes](reference/common-fixes.md) |
| Expected behavior for known PRs | [Evaluation cases](evals/cases.md) |

In the review rules, keep one decision per named rule. State the requirement,
then its exceptions and evidence requirements. Keep rule labels stable so other
instructions can refer to them. Historical examples illustrate rules; they do
not override an explicit rule or a documented exception. When changing a rule,
check related references and evaluation cases for conflicting guidance.

## Review checklist

Copy this checklist and tick it as you work:

```text
- [ ] 1. Run the diagnostic script and read all of facts.md
- [ ] 2. Interpret CI results and annotations
- [ ] 3. Apply every section of the review rules (3a-3k)
- [ ] 4. Verify each finding against evidence and write a concrete fix
- [ ] 5. Choose a verdict and write the report
```

## Step 1: Gather evidence

Requirements: `python3`, `git`, and an authenticated `gh`. The script downloads
`netkan.exe` once into `<skill dir>/bin/`. Windows runs it directly; Linux and
macOS require `mono`.

Run from the NetKAN checkout, or supply `--netkan-dir <path>`:

```bash
python "<this skill dir>/scripts/netkan_pr_diag.py" <PR_NUMBER>
```

The script prints the path to `facts.md`. Read the entire file. It contains:

- PR metadata, conversation, and the head content of each changed file, parsed
  into YAML documents.
- CI state, every `##[warning]` and `##[error]`, the CI-inflated `.ckan`, and the
  sandbox's `Showing N installed files` list.
- Local `netkan.exe` output and the resulting `.ckan`.
- ZIP analysis: layout, DLLs, `.version`, internal `.ckan`, ModuleManager syntax,
  heuristic tags and dependencies, craft files, licenses, bundled-mod candidates,
  and an approximate install.
- Cross-checks against `NetKAN/`: frozen or duplicate identifiers and `$kref`s,
  relationship targets, similar identifiers, SpaceDock name searches, other open
  PRs, and precedent netkans with the same dependencies.
- Host data: SpaceDock API responses, GitHub releases and the version-edit regex
  applied to real tags, metanetkan content, and the status page.

### Choose the release being reviewed

Use the latest release for every ZIP-based finding. The ZIP analysis's `Coverage`
line identifies the release each entry describes.

CI tests the release that was newest when the PR was pushed. If a newer release
exists, `facts.md` prints a warning and adds `LATEST UPSTREAM RELEASE` entries.
Mention when CI tested an older release. Use `--releases 3` to inflate older
releases too when their layouts may differ.

### Read the forum when other sources leave a question open

Read the forum thread when the SpaceDock description, README, and ZIP do not
settle permission, authorship, or dependencies. Find the URL in
`resources.homepage`, SpaceDock's `website`, or the bot PR's Homepage row. The
first post is the author's and usually lists the license, dependencies, and
downloads.

Plain HTTP requests get a 403, so use the Chrome tools. Navigate with
`mcp__claude-in-chrome__navigate`, then run this exact text with
`mcp__claude-in-chrome__javascript_tool`. It returns every post as author, date,
and body; `get_page_text` returns only one post. Close the tab afterward.

```javascript
[...document.querySelectorAll('article')].map(a=>((a.querySelector('h3')||{}).innerText||'?').trim()+' | '+((a.querySelector('time')||{}).getAttribute('datetime')||'')+'\n'+((a.querySelector('[data-role="commentContent"]')||a).innerText||'').trim()).join('\n\n---\n\n')
```

Later pages use `<thread URL>page/2/`.

For script failures, missing CI, inaccessible ZIPs, and metanetkans, read
[Uncommon cases](reference/uncommon-cases.md).

## Step 2: Interpret CI

| Result | Review action |
| --- | --- |
| Failure | Treat each `##[error]` or `FATAL` line as a BLOCKER. Give the metadata change that fixes it. See [CI validators](reference/ci-validators.md) for message meanings. |
| Success with warnings | Treat each warning as a lead. Confirm it against the ZIP and apply the relevant review rule. |
| No check | Say that CI has not run and use local inflation. The best available verdict is `LOOKS CORRECT (CI pending)`. |
| CI and local inflation disagree | Check which release each tested. The local run represents the latest release; a local FATAL on that release is a BLOCKER. The fix must work with both release layouts. State the release tested by each run. |

Common warning leads:

- `$vref is not ksp-avc, version file present`: add `$vref` under rule COMPAT-VREF.
- `ModuleManager syntax used without ModuleManager dependency`: add the dependency.
- `No plugin matching the identifier`: align the identifier with the DLL or folder,
  unless the author has a reason for the difference.
- `Unbounded future compatibility`: use a `.version` file or `ksp_version_max`.

Read `Showing N installed files` and compare it with the ZIP listing: those are
the files users actually receive. CI success does not establish that the metadata
is correct; most corrections in the sampled wrangler history were invisible to CI.

## Step 3: Apply the review rules

Read and apply **all sections (3a-3k)** of
[Review rules](reference/review-rules.md). They cover eligibility, identifiers,
hosts, versions, compatibility, installs, bundles, relationships, licenses,
metadata hygiene, and whether the mod could function.

Consult supporting references as needed:

- [Common fixes](reference/common-fixes.md): frequencies, reviewer quotes, and examples.
- [Spec cheatsheet](reference/spec-cheatsheet.md): field rules and valid values.
- [Bot generation](reference/bot-generation.md): fields the SpaceDock bot fills or guesses.
- [Documentation checklist](reference/doc-checklist.md): wiki checklist, tag vocabulary, labels.

## Step 4: Verify findings

Before reporting a correction:

1. Quote the exact supporting fact: a CI line, ZIP path, API field, or precedent.
2. Give a concrete replacement, rename, or deletion.
3. Check the PR conversation for an author explanation, and check relevant
   precedents. Resolve any contradiction using the rule's stated exceptions;
   otherwise drop the finding.

Label anything the evidence cannot establish as `not verified`. Never describe
ZIP contents you did not inspect.

## Step 5: Choose a verdict and write the report

### Severity

Use explicit severities in the review rules where given. For other findings:

| Severity | Meaning |
| --- | --- |
| BLOCKER | CI failure; broken or conflicting install, including overwriting another mod's files; eligibility/policy failure; or a relationship target that does not exist under any case. A frozen target alone is not a BLOCKER (REL-TARGETS). |
| SHOULD-FIX | A correction wranglers normally require before merging: identifier/folder mismatch without a reason, missing `$vref` or dependency, hard-coded host fields, wrong homepage, missing tags, wrong license variant, or a non-colliding install inside another mod's folder without matching precedent. |
| NICE-TO-HAVE | Style or future-proofing. |

Use judgement calls for decisions that need author input or where the rules call
for discussion. Include the evidence and options.

### Verdict

Apply the first matching row:

| Condition | Verdict |
| --- | --- |
| A gatekeeping rule (3a) fails, a required dependency is unindexable, or the sanity check (3k) finds the mod cannot work | `BLOCKED: <reason>`; still list any metadata corrections |
| Any other BLOCKER or any SHOULD-FIX exists | `NEEDS CORRECTIONS` |
| CI has not run | `LOOKS CORRECT (CI pending)` |
| Otherwise | `READY TO MERGE` |

### Required report format

Use this structure. [Example report](reference/example-report.md) illustrates the
expected depth for a different PR: follow its structure, never reuse its facts.
Write `None.` when there are no corrections.

````markdown
# NetKAN PR #<N>: <title>
<PR URL from facts.md>
**Verdict:** <READY TO MERGE | LOOKS CORRECT (CI pending) | NEEDS CORRECTIONS | BLOCKED: reason>
**CI:** <SUCCESS | FAILURE | not run> - <key annotation in one line>
**Mod:** <name> by <author>; hosts <spacedock id / github repo>; latest <version>; license <x>; PR by <login> (<bot|human>)
**Works?** <plausible | doubtful: reason | cannot work: reason | not verified> (static check only, 3k)

## Corrections needed
1. **[BLOCKER] <area>:** <what is wrong>. Evidence: <fact>. Fix:
   ```yaml
   <minimal corrected snippet or exact rename/delete instruction>
   ```

## Judgement calls / questions for the author
- <decision needed, evidence, and options>

## Checked and OK
- <one line per area that passed, with its key fact>
- <sanity-check basis, e.g. DLL references Assembly-CSharp 1.12 and all 14 PART cfgs have their .mu models>

## Facts
- facts: <path>; CI: <link>; ZIP listing: <path>
````

Keep the PR URL immediately below the title. Quote evidence for every correction.
You may finish with one combined proposed netkan block, clearly labelled as a proposal.
