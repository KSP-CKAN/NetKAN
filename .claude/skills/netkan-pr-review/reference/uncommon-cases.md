# Uncommon cases and fallback procedures

Read the section matching the problem. Apply [Review rules](review-rules.md) and
use [SKILL.md](../SKILL.md) for severity and verdict selection. These procedures
support a read-only report: commands that would change a PR or submission are
recommendations for its author or maintainer, not actions to perform.

When editing, keep the trigger, evidence to gather, and resulting decision in
the same section. Preserve command examples and field names when only rewording.

## Contents

- [Incomplete diagnostics](#fallback-script-incomplete-diagnostics)
- [Missing or unusable CI](#fallback-ci-missing-or-unusable-ci)
- [Unavailable or invalid ZIP](#fallback-zip-unavailable-or-invalid-archive)
- [Linux/macOS inflation](#fallback-mono-local-inflation-outside-windows)
- [Forum and README access](#fallback-forum-forum-or-readme-access)
- [Metanetkans](#remote-netkan-review-the-authoritative-file)
- [Internal CKAN files](#internal-ckan-metadata-shipped-in-the-zip)
- [Reviving frozen entries](#revive-frozen-reuse-an-existing-identifier)
- [Version ordering](#version-order-epochs-backports-and-prefixes)
- [Pinned releases and invalid templates](#template-host-replace-pinned-or-invented-hosting)
- [Copy/paste leftovers](#template-copy-check-that-the-file-describes-this-mod)
- [Version-file problems](#version-file-check-the-avc-input)
- [Multiple modules](#split-zip-several-mods-or-variants)
- [Craft and special destinations](#special-install-craft-missions-scenarios-and-gameroot)
- [Harmony and MiniAVC](#bundled-dlls-harmony-and-miniavc)
- [KSP2](#wrong-game-ksp2-submissions)
- [Unsupported hosts](#unsupported-host-unindexable-downloads)
- [Permission evidence](#permission-find-and-report-consent)
- [Sandbox install failures](#sandbox-failure-diagnose-dependency-and-file-conflicts)

## FALLBACK-SCRIPT: Incomplete diagnostics

If the script fails or omits evidence, gather the missing facts manually and
continue the checklist. Do not treat a tooling failure as proof of bad metadata.

### PR content and CI

```bash
gh pr view <N> -R KSP-CKAN/NetKAN --json title,author,body,files,commits,headRefOid,comments,reviews
gh pr diff <N> -R KSP-CKAN/NetKAN
gh api "repos/KSP-CKAN/NetKAN/contents/NetKAN/<Id>.netkan?ref=<headRefOid>" -q .content | base64 -d
gh pr checks <N> -R KSP-CKAN/NetKAN
gh run view --job <JOB_ID> -R KSP-CKAN/NetKAN --log
```

The check link contains the job ID. Search logs for `##[error]`, `##[warning]`,
and `Showing N installed files`.

### Inflation and duplicate checks

Create the cache and output directories before invoking NetKAN:

```bash
netkan.exe --game KSP --cachedir <dir> --outputdir <dir> <Id>.netkan
rg -i '<spacedock id or github repo>' NetKAN/
ls NetKAN/<Id>.*
```

On Linux/macOS, prefix the executable with `mono`. The script caches
[netkan.exe](https://ksp-ckan.s3-us-west-2.amazonaws.com/netkan.exe) in
`<skill dir>/bin/`; `NETKAN_EXE=<path>` overrides that location.
`--releases 3` also inflates older releases when their ZIP layouts may differ.

Without PyYAML, the diagnostic script uses a small built-in YAML parser. Anchors
or multiline flow mappings may parse incorrectly; compare parsed output with
the raw head content in `facts.md`.

### Host and ZIP evidence

```bash
curl -s https://spacedock.info/api/mod/<id>
curl -s "https://spacedock.info/api/search/mod?query=<name>"
gh api repos/<user>/<repo>/releases?per_page=5
```

For a ZIP the script did not analyze, such as an older release or second asset:

```bash
curl -sL -o x.zip "<asset url>"
python -c "import zipfile,sys;print('\n'.join(zipfile.ZipFile(sys.argv[1]).namelist()))" x.zip
python -c "import zipfile,sys;print(zipfile.ZipFile(sys.argv[1]).read(sys.argv[2]).decode('utf-8','replace'))" x.zip "<path in zip>"
```

SpaceDock download URLs have the form
`https://spacedock.info/mod/<id>/<name>/download/<version>`. `unzip -l <cached zip>`
is another way to list an archive. Use the downloaded release ZIP as evidence
for packaged content, rather than assuming the repository has the same layout.

## FALLBACK-CI: Missing or unusable CI

| State | Review action |
| --- | --- |
| No check | The PR may be new, or a maintainer may need to select "Approve and run" for a first-time contributor. Use local inflation. |
| Queued or running | State that status and use local inflation while reviewing. |
| Infrastructure failure | Docker pulls, caches, or API rate limits are not metadata findings. Note the failure and rely on local evidence. |

Without a completed usable check, do not claim CI success. For a check that has
not run, the best verdict is `LOOKS CORRECT (CI pending)`; actual corrections
still take precedence.

## FALLBACK-ZIP: Unavailable or invalid archive

If the ZIP cannot be inspected, mark install, bundling, `$vref`, and license-file
checks `not verified`.

If the download also fails in CI, report the relevant BLOCKER: invalid ZIP,
unsupported compression, HTTP 404/5xx, or an HTML landing page instead of a ZIP.
The host must serve an ordinary ZIP, not RAR/7z or exotic compression.

A GitHub release without an asset can crash inflation at `assets.First()`.
Propose dropping that host, asking for a release ZIP, or using
`x_netkan_github: {use_source_archive: true}` only when the archive contains a
usable mod layout and the install finds its stable inner folder (HOST-FALLBACK).

## FALLBACK-MONO: Local inflation outside Windows

`netkan.exe` targets .NET Framework. Linux/macOS require
`mono netkan.exe ...`.

Without mono, the script skips local inflation and uses the CI-inflated `.ckan`.
If CI has not run either, it inspects direct host downloads: SpaceDock's latest
version and GitHub's latest release asset. State which evidence was available.

## FALLBACK-FORUM: Forum or README access

The forum returns 403 to plain HTTP clients such as curl and WebFetch. Use the
Chrome workflow and exact JavaScript snippet in [SKILL.md, step 1](../SKILL.md).

- `get_page_text` returns one post, often the newest or first unread; do not
  mistake that for the whole thread.
- The numeric topic ID matters; the URL slug can differ.
- Additional pages use `<thread URL>page/N/`.
- `find` / `computer` screenshots are a slower fallback.

If Chrome is unavailable, use the SpaceDock description, GitHub README, ZIP
README, `.version`, and changelog. Fetch the GitHub README with:

```bash
gh api repos/<u>/<r>/readme -q .content | base64 -d
```

Label questions requiring the thread `not verified; check the forum thread`.

## REMOTE-NETKAN: Review the authoritative file

**Trigger:** `$kref: '#/ckan/netkan/<url>'`.

The local file contains an identifier, remote reference, and optional overrides.
Review the remote content shown under "Metanetkan" in facts using the normal
checklist. The outer file skips license validation.

Check that the remote file:

- Is not itself a metanetkan.
- Uses the same identifier as the local file.
- Is available as a raw file on a stable branch.

For a single mod, an internal `.ckan` usually keeps metadata and releases aligned
more simply. Suggest that as a judgement call, not a required correction.

## INTERNAL-CKAN: Metadata shipped in the ZIP

An internal `.ckan` adds properties to the release's metadata. Values already set
in the netkan win. If the internal file is meant to own `depends`, `recommends`,
or `$vref`, remove the duplicate netkan field in the proposed correction.

Check that the internal file is inside an installed folder and its identifier
matches. For a multi-module ZIP, use explicit installs so each module selects
its own internal file. Multiple internal `.ckan` files selected for one inflation
are an error; separate the module selections rather than applying all files.

## REVIVE-FROZEN: Reuse an existing identifier

If the submitted mod already has `NetKAN/<Id>.frozen` (same host ID, repository,
or folder), propose reusing that identifier. Remove/rename the frozen twin as
part of revival; CI rejects a live entry with a same-named frozen twin.

Modernize format, `$kref`, `$vref`, tags, install, and relationships while retaining
identity for existing users. Do not create a second identifier. This procedure
is for reviving the mod itself, not for a new mod that merely depends on a frozen
entry; REL-TARGETS requires no unfreezing in that case.

## VERSION-ORDER: Epochs, backports, and prefixes

| Situation | Applicable control |
| --- | --- |
| A new version sorts below the previously indexed release | Automatic epoch bumping; `x_netkan_epoch: N` sets an explicit floor. For a new submission, this matters only if older CKAN-meta history exists, such as a frozen entry. |
| Intentional backports | `x_netkan_allow_out_of_order: true` |
| Already indexed with a `v` prefix | Preserve it with `x_netkan_force_v: true` in every host document. `v1.2` sorts above `1.3`. |
| SpaceDock versions contain spaces, dates, or words, such as `1.0 beta` or `2024.05.01` | Check ordering and apply any needed `x_netkan_version_edit` consistently across host documents. |

A shared `v`/`V` prefix is not itself a correction for this skill. Apply
VERSION-MATCH before proposing normalization.

## TEMPLATE-HOST: Replace pinned or invented hosting

A hard-coded `download` / `version` without `$kref` pins one release. An invented
structure such as `x_netkan: {github: {repository: ...}}` does not create updates.
Propose the supported host reference, for example
`#/ckan/github/<user>/<repo>` or `#/ckan/spacedock/<id>`.

A document containing both `$kref` and `download` fails CI.

## TEMPLATE-COPY: Check that the file describes this mod

A copied template may still describe the author's other mod. Compare the host
target and ZIP with the identifier, name, tags, relationships, and install.
If they describe different mods, propose rewriting the template for this mod.

## VERSION-FILE: Check the AVC input

| Problem | Review action |
| --- | --- |
| Invalid JSON or wrong `VERSION` / `KSP_VERSION*` shape | `$vref` may fail silently. Request an upstream fix using the [AVC validator](https://github.com/DasSkelett/AVC-VersionFileValidator); omit `$vref` until usable. Check the expected `{MAJOR, MINOR, PATCH}` structure rather than trusting a bare version string. |
| Several candidate files under the install root | Disambiguate with `$vref: '#/ckan/ksp-avc/<path>/<file>.version'` to avoid "Too many .version files". |
| Only version file belongs to a bundled mod | Do not use it for this mod's `$vref`. |
| `KSP_VERSION` 2.x or `swinfo.json` | Check WRONG-GAME. |
| `.version` `URL` points to a removed branch | Report the broken `remote-avc` reference. |

## SPLIT-ZIP: Several mods or variants

Independent mods, mutually exclusive variants (2D/3D, 8k/16k, Stock/RSS), and a
core plus optional packs need separate netkans. Each module gets its own
identifier and install selection, filtering out other modules as needed.

Depend on the core where required. Use `conflicts` for exclusive variants and a
common virtual `provides` name when dependents can use any variant. Several
netkans may share one download URL.

## SPECIAL-INSTALL: Craft, Missions, Scenarios, and GameRoot

| Content | Destination or limitation |
| --- | --- |
| Player-launchable craft | `Ships/VAB` or `Ships/SPH`; select folders rather than writing one stanza per craft. |
| Sample craft not intended for installation | Exclude with `filter_regexp: \.craft$`. |
| Contract/mission-prop craft | Preserve the GameData-relative path referenced by `craftURL` or similar CFG fields. Do not relocate it to silence a warning. See INSTALL-CONTENT. |
| Shipped subassemblies/thumbnails | Use their appropriate Ships layout, including adjacent `Ships/@thumbs` content where present. |
| Missions and Scenarios | Their corresponding `install_to` destinations. |
| GameRoot | Requires a strong reason. Metadata cannot conditionally choose `KSP_Data` versus `KSP_x64_Data`; discuss `Blocked-on-CKAN-feature`. |

## BUNDLED-DLLS: Harmony and MiniAVC

A bundled `0Harmony.dll` without `provides: [Harmony1]` triggers a CI error.
Prefer declaring `depends: Harmony2` and filtering out the bundled DLL.

The validator ignores `MiniAVC.dll` inside the mod's own folder. Filter out a
separate MiniAVC folder at GameData level.

## WRONG-GAME: KSP2 submissions

`swinfo.json`, `BepInEx/plugins`, or `.version` KSP 2.x indicate KSP2; SpaceDock
game IDs other than 3102 also require checking the game. KSP2 belongs in
`KSP-CKAN/KSP2-NetKAN`, with verdict `BLOCKED` here.

## UNSUPPORTED-HOST: Unindexable downloads

Supported references include SpaceDock, GitHub, GitLab source archives,
Gitea/Forgejo, SourceForge, Jenkins, plain HTTP with a version file, remote
`.version` (`ksp-avc`), and metanetkans. See [Spec cheatsheet](spec-cheatsheet.md)
for syntax.

Google Drive, Dropbox, MEGA, Discord/forum attachments, Nexus, CurseForge's retired
API, and paywalled downloads are not indexable by this workflow. Report
`BLOCKED` and discuss `Blocked-on-other`; suggest SpaceDock or GitHub release ZIPs.

## PERMISSION: Find and report consent

For bot PRs, compare SpaceDock `author` / `shared_authors` with the GitHub owner,
`.version` `GITHUB.USERNAME`, README/LICENSE copyright, and forum author. The CKAN
checkbox counts only when selected by the author or maintainer.

For third-party human PRs, look for author approval in a forum post, GitHub
comment, or supplied Discord screenshot. It normally belongs in the PR body,
but a missing body link does not mean approval is absent. An author's CKAN
announcement or a post thanking the submitter as a collaborator can supply the
needed context. Quote the evidence under Checked and OK and request its link
under judgement calls.

If no approval is found, report `BLOCKED` / `Blocked-on-mod-author`. The standard
request is:

> CKAN as a matter of policy only adds mods if the authors agree. Have these authors agreed? If so, please add a link to where they agreed in the body of this pull request.

Authors on the [opt-out list](https://github.com/KSP-CKAN/CKAN/blob/master/policy/Opt-out-list.md)
are never indexed. An explicit refusal remains effective until revoked.

## SANDBOX-FAILURE: Diagnose dependency and file conflicts

The `Installing ...` step resolves `depends` for the newest compatible game
version. Match the failure to a concrete proposed correction:

| Failure | Proposed correction |
| --- | --- |
| Dependency supports only older game versions | Consider a PR-body `ckan compat add 1.10 1.11 1.12` directive to simulate user settings. |
| Dependency identifier does not exist | Correct the identifier. |
| Optional `recommends` pulls in a conflict | Use `suggests` for the optional integration. Do not soften a genuinely required dependency just to pass CI. |
| Two modules write the same file | Exclude a bundled copy, or split modules with appropriate relationships. |

A PR-body `ckan install A B` directive requests an additional combined install test.
