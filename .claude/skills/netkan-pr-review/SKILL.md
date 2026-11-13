---
name: netkan-pr-review
description: Reviews a KSP-CKAN/NetKAN pull request that adds a new mod and reports whether the netkan is correct or which corrections it needs. Use when asked to review, check, vet, or look at a NetKAN PR, a netkan file, or a new mod submission by PR number. Read-only, never edits the PR.
---

# Reviewing a NetKAN PR (diagnostic only)

Act as a CKAN metadata wrangler reviewing one PR to `KSP-CKAN/NetKAN`. Output a report; never
edit files, push, comment, or merge. Input: a PR number (or URL).
Scope: PRs that add a new mod. For a PR that edits an existing netkan, judge the resulting file
as if it were a new submission; ignore CKAN-meta history.

Requirements: `python3`, `git`, an authenticated `gh`. `netkan.exe` is downloaded once into
`<skill dir>/bin/` (Windows runs it natively; Linux/macOS need `mono`).

Copy this checklist and tick it as you go:
```
- [ ] 1. Run the diagnostic script; read facts.md completely
- [ ] 2. CI state and annotations interpreted
- [ ] 3. Checklist 3a-3k applied to the facts
- [ ] 4. Every finding re-checked against facts.md (evidence + concrete fix)
- [ ] 5. Report written in the required format
```

## Step 1: gather facts

```bash
python "<this skill dir>/scripts/netkan_pr_diag.py" <PR_NUMBER>
```
Run from inside the NetKAN checkout (or add `--netkan-dir <path>`). It prints the path of
`facts.md`; read all of it. It holds: PR metadata and conversation; head content of each changed
file, parsed into YAML documents; CI state with every `##[warning]`/`##[error]`, the CI-inflated
`.ckan`, and the sandbox `Showing N installed files` list; local `netkan.exe` output and `.ckan`;
ZIP analysis (layout, DLLs, `.version`, internal `.ckan`, ModuleManager syntax, heuristic
tags/depends, crafts, license files, bundled-mod candidates, approximate install); cross-checks
against `NetKAN/` (frozen/duplicate identifiers and `$kref`s, relationship targets, similar
identifiers, SpaceDock name search, other open PRs, precedent netkans with the same
dependencies); host data (SpaceDock API, GitHub releases with the version-edit regex applied to
real tags, metanetkan content, status page).

The "Coverage" line at the top of the ZIP analysis says which release each ZIP entry describes.
CI tests only the release that was newest when the PR was pushed; if the author released again
since, facts.md prints a WARNING and adds `LATEST UPSTREAM RELEASE` entries. Base every ZIP-derived
finding on the latest release, and mention when CI saw an older one. (`--releases 3` also inflates
older releases when the layout may differ between versions.)

For the forum thread (`resources.homepage`, the SpaceDock `website`, or the bot PR's Homepage
row) use the Chrome tools; plain HTTP fetches get a 403. `mcp__claude-in-chrome__navigate` to the
URL, then run `mcp__claude-in-chrome__javascript_tool` with this exact text (it returns every post
as `author | date` + body; `get_page_text` returns only ONE post), then close the tab:
```javascript
[...document.querySelectorAll('article')].map(a=>((a.querySelector('h3')||{}).innerText||'?').trim()+' | '+((a.querySelector('time')||{}).getAttribute('datetime')||'')+'\n'+((a.querySelector('[data-role="commentContent"]')||a).innerText||'').trim()).join('\n\n---\n\n')
```
Later pages are `<thread URL>page/2/`. Read the thread whenever permission, authorship, or
dependencies are not settled by the SpaceDock description, README, and ZIP; the first post is the
author's, and it usually names the license, dependencies, and download links.

If the script fails, CI has not run, the ZIP cannot be fetched, or the PR is a metanetkan, see
[reference/uncommon-cases.md](reference/uncommon-cases.md).

## Step 2: CI first

- **FAILURE**: each `##[error]`/`FATAL` line is a BLOCKER; state the metadata change that fixes it
  (message meanings: [reference/ci-validators.md](reference/ci-validators.md)).
- **SUCCESS with warnings**: each `##[warning]` is a lead to confirm with the ZIP facts. "$vref is
  not ksp-avc, version file present" -> add `$vref`; "ModuleManager syntax used without
  ModuleManager dependency" -> add the dependency; "No plugin matching the identifier" -> rename
  the identifier to the DLL/folder unless the author has a reason; "Unbounded future
  compatibility" -> `.version` file or `ksp_version_max`.
- **No check**: say so; use the local inflation instead (verdict at most `LOOKS CORRECT (CI pending)`).
- **CI SUCCESS but local inflation FATAL** (or the reverse): the two ran on different releases.
  The local run is today's truth; its FATAL on the latest release is a BLOCKER, and the fix must
  work for the ZIP layouts of both releases. Say which release each one tested.
- Read `Showing N installed files`: it is what users get. Compare with the ZIP listing.

A green check is necessary, never sufficient: in the sampled history, essentially every
correction a wrangler made was invisible to CI.

## Step 3: checklist

Frequencies, reviewer quotes, and examples for each item: [reference/common-fixes.md](reference/common-fixes.md).
Field rules and valid values: [reference/spec-cheatsheet.md](reference/spec-cheatsheet.md).
What the SpaceDock bot fills in and where it guesses: [reference/bot-generation.md](reference/bot-generation.md).
Wiki checklist, tag vocabulary, labels: [reference/doc-checklist.md](reference/doc-checklist.md).

### 3a. Gatekeeping (BLOCKED if any fails)
- **Permission.** Bot PR: SpaceDock uploader (`author`/`shared_authors`) must be the mod's
  author/maintainer; compare with the GitHub owner. Human PR by a third party needs the author's
  approval: a link in the PR body, or a forum/GitHub post you found yourself (then ask for the
  link to be added, as a judgement-call item, not a BLOCKER). Nothing found -> BLOCKED. An
  author's own "not on CKAN until it is stable" statement is a refusal until they revoke it.
  Opt-out-list authors are never indexed.
- **KSP1.** SpaceDock `game_id` 3102, `.version` `KSP_VERSION` 1.x, no `swinfo.json`.
- **Not a duplicate.** Same SpaceDock id / GitHub repo / folder / DLL already indexed, a `.frozen`
  twin (reuse it), a case-insensitive or near identifier, a SpaceDock search hit under another id,
  a status-page entry, or another OPEN PR for the same mod (facts: "OTHER OPEN PRs"; one PR per
  netkan, normally the earlier or the author's own). Forks of indexed mods need
  `conflicts`/`provides`/`replaced_by` decisions.
- **Indexable host** with a real ZIP asset (see spec-cheatsheet for `$kref` hosts and options).

### 3b. Identifier
- `^[A-Za-z0-9][A-Za-z0-9-]+$`, equal to the filename stem in every document.
- Core name only: no version, game version, "WIP", author/host names, subtitles. Bot identifiers
  are the SpaceDock title minus punctuation and need pruning whenever the title has a colon, pipe,
  or parenthetical.
- Should equal the GameData folder (then the default install stanza applies and manual installs
  are detected) or, for plugins, the DLL base name. Mismatch without a stated reason: SHOULD-FIX.
  Follow sibling conventions in `NetKAN/` (`Foo-Textures`, `TURD-Bar`).

### 3c. Hosting and documents
- SpaceDock + GitHub with releases -> both documents (fallback downloads). Drop a GitHub document
  whose releases have no asset. GitHub's automatic source zip (`use_source_archive`) is not a
  packaged mod: it wraps the repository in `<repo>-<sha>/`, so accept it only when the ZIP facts
  show the mod folder inside and the install stanza uses `find` on that folder.
- Per-document fields are applied to each document BEFORE merging, so repeat them in EVERY
  document: `$vref`, `x_netkan_version_edit`, `x_netkan_epoch`/`force_v`, `license` when that
  host cannot supply it, `install` when the two ZIPs differ. Missing `$vref` in one document is
  SHOULD-FIX (house convention "vref in both sections"), not a CI error. Tags, relationships and
  name may live in one document (house style: the SpaceDock one).
- GitHub: `archived`/`fork` (canonical repo?), `prereleases`, `asset_match` when a release has
  several ZIPs. `version_edit_applied` in facts shows the version each tag yields; a `null`
  means `strict: true` fails on that tag.

### 3d. Version string
- The only requirement is consistency: every host must yield the identical string for a release
  ("Generated 2 modules but only 1 requested: X on github.com; vX on spacedock.info" is the
  failure). Fix a mismatch with the same `x_netkan_version_edit: ^v?(?<version>.+)$` (or `[vV]`)
  in every document, including the SpaceDock one. A `v`/`V` prefix that all hosts share is fine;
  do not request a version edit just to strip it.
- Hard-coded `version`/`download` with a `$kref` is wrong. Epoch and out-of-order cases:
  uncommon-cases.md.

### 3e. Compatibility
- ZIP ships an installed `.version` -> `$vref: '#/ckan/ksp-avc'` in every document. Several
  `.version` files -> path form. `.version` must be this mod's, valid JSON, `{MAJOR,MINOR,PATCH}`
  objects (facts prints `.version note` lines).
- No hard-coded `ksp_version*` when `$vref` or SpaceDock provides compatibility.

### 3f. Install stanza (use the ZIP facts)
- Install exactly the mod's own folder(s) (+ `Ships/...` for craft files the player is meant to
  fly — but NOT a contract/mission-prop craft referenced by a `craftURL`/similar GameData-relative
  path in a `.cfg`; that one must stay in GameData or the reference breaks: see
  spec-cheatsheet.md "install"). Compare the `Showing N installed files` list and the approximate
  install with the ZIP listing.
- Identifier == sole GameData folder -> no `install` block at all (delete the redundant default).
- `find: ''` -> BLOCKER, choose the folder. `find: GameData`, release-specific `file:` paths,
  version-numbered or space-containing wrapper folders -> use `find` on the stable inner folder,
  `install_to: GameData`.
- A *stable* author/publisher namespace folder shared across that author's own mods (e.g.
  `GameData/AnaAerospace`, `GameData/SterlingSystems`) is not the same as the unstable wrapper
  case above — do not collapse it away. `find: <namespace>, install_to: GameData` makes the whole
  namespace folder one of this module's owned install paths, which a sibling mod by the same
  author reusing that same folder would also claim, conflicting. Instead put the namespace folder
  in `install_to` and `find` only the mod-specific inner folder (same on-disk result, but this
  package only owns its own subfolder) — see the `SterlingSystems*` netkans (`find: Engines,
  install_to: GameData/SterlingSystems`) for house precedent.
- Installing into another indexed mod's own folder (`find`/`file`/`install_to` naming `TUFX`,
  `Kopernicus`, etc.) is a BLOCKER when the path collides with a file the target mod itself ships
  (CKAN cannot overwrite another mod's files, see spec-cheatsheet.md "install"). For a
  non-colliding add-on file (e.g. a uniquely named profile/patch), default to SHOULD-FIX and
  recommend the mod's own folder instead — most frameworks that load drop-in files (TUFX profiles,
  MM patches) scan all of `GameData`, so nothing is lost by not nesting inside the target's
  directory. Only call it OK when sibling netkans that *also install into that folder* do the same
  thing — `grep -l "name: <Target>" NetKAN/*.netkan` then read each match's `install:` stanza;
  merely sharing the `depends` is not a matching precedent (one real hit among many non-matching
  siblings is an outlier, not a precedent).
- Exclude source code, `.pdb`, `__MACOSX`, `Thumbs.db`, `.git*`, optional `Extras`, and
  player-launchable craft files under GameData (`filter`/`filter_regexp`) — but not a contract-prop
  craft (see above). Junk inside the mod's own folder is fine.

### 3g. Bundled third-party mods
Any folder/DLL in the ZIP that is another mod (`bundled_candidates` in facts: ModuleManager,
Toolbar/ToolbarControl, ClickThroughBlocker, Kopernicus, B9PartSwitch, Firespitter, CRP, MiniAVC
folder, Waterfall, Scatterer, TUFX, 0Harmony ...) must be excluded from the install AND declared
in `depends` (or `suggests`/`recommends` if optional, per 3h). Installing a copy conflicts with the
real mod: BLOCKER.

### 3h. Relationships
- `depends`: everything the mod cannot run without. Evidence: MM syntax (ModuleManager), cfg
  `:NEEDS`/`:FOR`/MODULE names (Kopernicus, Waterfall, B9PartSwitch, TUFX, ContractConfigurator,
  KerbalKonstructs, Scatterer/EVE, Harmony2, ToolbarController/ClickThroughBlocker), the
  SpaceDock description/README "requires", the `.version`, and sibling mods. The bot finds only
  ModuleManager plus one obvious framework; missing dependencies are the single most frequent fix.
  Add `min_version` when a newer dependency release is required. The depends/recommends line is a
  functional test on the dependent mod itself, not on whether anything errors without the target:
  `depends` = "you cannot use this mod without X" (it is completely non-functional/purposeless
  without X, even though nothing crashes) — this includes a content-only pack that exists purely
  to be fed into another mod's mechanism, e.g. a decal/flag/texture pack meant to be selected
  through ConformalDecals' menu, which has zero function on its own. `recommends` = "you would not
  normally install this without X" — near-mandatory in practice, but the mod still does something
  by itself or there's a legitimate reason to skip X. A content-only pack that is inert without its
  target meets the `depends` test even when a precedent netkan for the same category uses the
  softer `recommends` — flag that precedent as potentially soft rather than copying it silently
  (e.g. GRIT, a ConformalDecals decal pack, PR #11400: correctly `depends`, not `recommends`, even
  though the closest precedent `ISO-7010-Decals.netkan` — the same "flags pack for ConformalDecals"
  pattern — uses `recommends`).
- Plugin DLL evidence: when ilspy MCP tools are available, run `get_assembly_attributes` and
  `list_assembly_references` on each DLL in the ZIP rather than just string-searching. A
  `KSPAssemblyDependency` attribute or a reference to another mod's assembly is real evidence, but
  only when it appears on the identifier's own main DLL (the one matching the identifier/GameData
  folder) — a small integration/bridge DLL that exists purely to talk to an optional companion mod
  turning up the same reference does NOT make it a hard dependency of the whole package; that
  belongs in `suggests`, not `depends`.
- Every relationship name must be an existing identifier, exact case (facts: `ok`/`virtual`/
  `dlc`; `UNKNOWN`/`WRONG CASE` (the identifier does not exist under any case) are BLOCKERs;
  unindexable dependency (paid/Patreon-gated, deliberately not indexed) -> BLOCKED). A `frozen`
  target is NOT itself an issue and needs no fix — freezing only stops future re-inflation,
  CKAN-meta keeps serving whatever version was last indexed, so existing installs and new
  dependents still resolve against it — but it IS a signal to look closer: confirm the freeze was
  for inactivity and not because the host listing/repo is gone or the author announced abandonment
  (then it's a real problem, DUP-02-style). Note a frozen dependency under judgement calls for
  visibility; never propose unfreezing it as a correction. `only in CKAN-meta` (metadata exists
  with no current NetKAN entry at all) still needs discussion. Point at current identifiers, not
  superseded ones.
- Debian-style semantics, and default to `suggests`: `recommends` means "you would not normally
  install this mod without also installing the target" (near-mandatory in practice, the resolver
  installs it by default); `suggests` means "consider also installing the target" (an optional
  enhancement or integration the user can take or leave). Most companion mods mentioned in a
  description/README ("works great with X", "adds support for X", "compatible with X") are
  `suggests`, not `recommends` — reserve `recommends` for cases where the mod is crippled,
  visually broken, or missing core content without the other mod. `supports` = this mod is offered
  when the other is installed (often used backwards, i.e. authors write it meaning `suggests`);
  `conflicts` for same-folder/same-DLL/incompatible mods and forks of indexed mods.
- Copy house style from the precedent netkans in facts (e.g. `KerbalChangelog` is `suggests`,
  profile packs `depends` on their framework, "Redist" modules carry no `recommends`), but when
  precedent itself uses `recommends` for what reads like an optional integration, flag it as a
  judgement call toward `suggests` rather than copying it silently.

### 3i. License
- Valid spec string only (list in spec-cheatsheet); SpaceDock free text is the usual CI FATAL.
- Must match the ZIP's LICENSE / README / GitHub `license_spdx` / SpaceDock field. Mixed
  licensing or "All rights reserved" -> `restricted`; genuinely unknown -> `unknown`.
- Do not restate a license the host supplies; do set it in a document whose host cannot.

### 3j. Tags, name, resources, hygiene
- Tags from the Suggested Tags vocabulary only; curate the bot's structural tags (`config` for any
  cfg, `plugin` for any DLL) and add descriptors from the description. No tags: SHOULD-FIX.
- Do not hard-code `name`, `abstract`, `author`, `resources.*`, `ksp_version` that the host
  provides; do set `resources.homepage` to the forum thread when the host lacks it, and `author`
  when the uploader is not the author (include original authors of continued mods).
- Bot-generated fields must not be hand-written: `spec_version`, `release_status`,
  `download_size`, `download_hash`, `download_content_type`, `install_size`, `release_date`,
  `x_generated_by`, `x_netkan_version_pieces` (full rationale per field: spec-cheatsheet.md
  "Bot-generated fields"). Finding one is usually a sign the file was copied from an inflated
  `.ckan` rather than written as a template - SHOULD-FIX, delete the field.
- YAML preferred; `$kref`/`$vref` quoted; no mixed JSON/YAML; no misspelled keys (`licence`,
  `dependencies`, `version_min`); no duplicate relationship entries; `x_via` may stay.
- Internal `.ckan` in the ZIP: the netkan must not restate what it provides (uncommon-cases.md).

### 3k. Could it work at all? (quick sanity check, not a code review)
Spend a few minutes at most, using only what facts.md and the ZIP listing already show. The
question is "is there any reason this cannot function", not "is it good". Look for:
- **Empty or wrong payload:** ZIP has no GameData content, only source/docs/screenshots, or the
  `Showing N installed files` list is empty, tiny, or lacks the mod's DLL/parts/cfg that the
  description promises.
- **Plugin mods:** a DLL exists (not just a `.cs`/`.csproj`); with ilspy tools, `list_assembly_references`
  shows `Assembly-CSharp`/`UnityEngine` (KSP1), not `Assembly-CSharp` from KSP2 or a different
  engine, and the target framework is one KSP1 loads (net4x/netstandard2.0; a `net6.0`+ DLL will
  not load). A DLL that references another mod's assembly with no matching `depends` goes to 3h.
- **Part/content mods:** every `.cfg` `PART` has its `mesh`/`MODEL` file (`.mu`/`.dae`) and
  textures in the ZIP; `*.cfg` files are not all empty or obviously broken (unbalanced braces,
  a bare template left unedited).
- **Patch-only mods:** MM patches target something that exists (KSP stock or a declared
  dependency); a patch for a mod that is neither installed nor a dependency does nothing.
- **Version fit:** `.version`/SpaceDock KSP range is not obviously unusable for KSP1 (a lone
  KSP 0.x/1.0-1.2 mod with a plugin DLL is likely broken on current KSP: judgement call).
- **Placeholder or joke/test uploads:** description or files show it is a template, "test", or
  an empty stub.
- **Author statements:** the SpaceDock description, README, or forum thread says it is broken,
  WIP-unplayable, or requires something unavailable (paid, a removed mod).

Outcome, one of: `plausible` (nothing found), `doubtful: <reason>` (list as a judgement call
with the evidence), or `cannot work: <reason>` (a BLOCKER; verdict `BLOCKED: mod cannot
function`). Never claim it was tested in game; say "static check only". If a check needs
something facts.md lacks (e.g. DLL references without ilspy), write "not verified".

## Step 4: verify before reporting

For every finding: (1) quote the exact fact (CI line, ZIP path, API field, precedent) that
supports it; (2) write the concrete replacement; (3) check it does not contradict a precedent or a
stated author reason in the PR conversation. Drop findings that fail any of the three. Mark
anything the facts could not establish as "not verified".

## Step 5: report

Severity: **BLOCKER** = CI failure, broken/conflicting installs (incl. a path that collides with
another mod's own files), policy (permission, duplicate, KSP2, unindexable host), nonexistent
relationship target (does not exist under any case — NOT a merely `.frozen` one, see 3h).
**SHOULD-FIX** = what wranglers fix before merging (identifier/folder
mismatch, missing `$vref` or dependency, host-provided fields hard-coded, wrong homepage, missing
tags, wrong license variant, a non-colliding file installed into another mod's folder without a
real matching precedent). **NICE-TO-HAVE** = style and future-proofing.
Verdict, first rule that matches:
1. a 3a gatekeeping item fails (permission, KSP2, duplicate incl. another open PR, unindexable
   host or dependency) or 3k finds the mod `cannot work` -> `BLOCKED: <reason>`, even if
   metadata fixes are also listed;
2. any other BLOCKER or any SHOULD-FIX -> `NEEDS CORRECTIONS`;
3. CI has not run -> `LOOKS CORRECT (CI pending)`;
4. otherwise -> `READY TO MERGE`.

ALWAYS use this exact structure. [reference/example-report.md](reference/example-report.md) shows
the expected depth for a DIFFERENT PR: copy its structure, never its facts.

```markdown
# NetKAN PR #<N>: <title>
<PR URL, from facts.md, right below the title so it's the first thing visible>
**Verdict:** <READY TO MERGE | LOOKS CORRECT (CI pending) | NEEDS CORRECTIONS | BLOCKED: <reason>>
**CI:** <SUCCESS | FAILURE | not run> - <one line: key annotation>
**Mod:** <name> by <author>; hosts <spacedock id / github repo>; latest <version>; license <x>; PR by <login> (<bot|human>)
**Works?** <plausible | doubtful: <reason> | cannot work: <reason> | not verified> (static check only, 3k)

## Corrections needed
1. **[BLOCKER] <area>:** <what is wrong>. Evidence: <fact>. Fix:
   ```yaml
   <minimal corrected snippet or exact rename/delete instruction>
   ```
(If none: "None.")

## Judgement calls / questions for the author
- <decision needed, with the options>

## Checked and OK
- <one line per area that passed, with its key fact; include the 3k "could it work" basis, e.g.
  "DLL references Assembly-CSharp 1.12, all 14 PART cfgs have their .mu models">

## Facts
- facts: <path>; CI: <link>; ZIP listing: <path>
```

Quote evidence for every correction; never describe ZIP contents you did not see. Optionally end
with one combined "proposed netkan" block labelled as a proposal.
