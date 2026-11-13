# NetKAN CI: checks, messages, and limits

Use this reference to interpret the "Inflate netkans" check. CI establishes
whether metadata can inflate and install in its sandbox; a reviewer still needs
the ZIP, author evidence, and [Review rules](review-rules.md).

Sources: `.github/workflows/inflate.yml`, `KSP-CKAN/xKAN-meta_testing`
(`ckan_meta_tester.py`), and `KSP-CKAN/CKAN/Netkan/Validators/*.cs`.

When updating, keep literal messages in the validator matrix. Put exceptions
beside the affected check. CI message levels are not the skill's finding
severities; choose the report severity using [SKILL.md](../SKILL.md).

## CI-PIPELINE: What runs for a PR

| Stage | What happens | Where to inspect it |
| --- | --- | --- |
| Lint | Relaxed `yamllint` checks added/modified `.netkan` files between merge-base and HEAD. New files must be in `NetKAN/`, with no same-named `.frozen` twin. | Lint output |
| Inflate | `netkan.exe --game KSP --highest-version <from CKAN-meta> <file>` inflates the latest release and runs validators. | `Inflating NetKAN/<id>.netkan`, then the generated `.ckan` JSON |
| Diff | Compare with CKAN-meta when that identifier/version already exists. An empty diff skips the install step. | `Diffing <name> <version>` |
| Install | Install the mod and dependencies in a dummy game using the newest compatible game version, then run `ckan show`. Unresolvable dependencies, conflicts, and file collisions fail this step. | `Installing <name> <version>`, `Showing N installed files:`, compatibility table |
| Upload | Save generated metadata. | Artifact `metadata-<PR>` |

"Latest" means the newest release when the PR was last pushed. CI does not rerun
just because upstream publishes another release. Compare the diagnostic
`Coverage` line and local inflation with CI before using its ZIP evidence.

Validators run per host document. A two-host file can print the same warning
twice; `facts.md` may summarize that with `x2`. Count it as one finding.

## CI-DIRECTIVES: PR-body commands understood by the tester

These are proposed changes for a maintainer or PR author. The review skill does
not edit the PR body.

| Directive | Effect |
| --- | --- |
| `ckan compat add 1.10 1.11 1.12` | Simulate user compatibility settings so dependencies with narrower game-version ranges can be installed. |
| `ckan install ModA ModB=1.2` | Run additional install tests after the main test. |
| `#overwrite_cache` | Redownload a release asset that upstream replaced. |

An empty PR body generates a warning for every file.

## CI-MESSAGES: Validator matrix

Warnings and errors appear as `##[warning]` / `##[error]` annotations in the job
log and PR Files tab. Warnings alone do not fail the job; `ERROR` / `FATAL` lines
do. The messages below are abridged; use the actual log line as report evidence.

| Check | Level | Message (abridged) |
|---|---|---|
| identifier missing | error | Metadata must have an identifier property |
| identifier chars | error | CKAN identifiers must consist only of letters, numbers, and dashes, and must start with a letter or number |
| identifier != filename stem | error | Have metadata for X, but wanted Y |
| `$kref` malformed / both `$kref` and `download` / neither | error | Invalid $kref / has a $kref and a download field / has no $kref field |
| `download` without `version` | error | expects a version when a download url is provided |
| `x_netkan_override` shape | error | Netkan overrides require an array / a version / a delete or override section |
| spec_version format & feature gating | error | spec version must be 1 or in the 'vX.X' format; spec_version vN+ required for ... |
| license not in list | error (FATAL) | License X should match spec / The licence X is invalid |
| relationship `name` invalid / `version_min` typo / non-object entries | error | ... is not a valid CKAN identifier / correct form is 'min_version' |
| `install_to` invalid, install property empty, un-normalised path | error | install stanza missing `install_to` / Path ... is not normalized |
| install stanza matches nothing | error | Module contains no files matching: ... |
| GameData nested inside GameData | error | GameData directory found within GameData |
| two files to same destination | error | Multiple files attempted to install to: |
| no compatible game version | error | doesn't match any valid game version |
| JSON schema violation | error | Schema validation failed |
| Harmony DLL bundled without `provides: [Harmony1]` | error | Harmony DLL found at ..., but Harmony1 is not in the provides list |
| `kind` gating | error | spec_version 1.6+ required for kind 'metapackage' ... |
| tags missing | warning | Tags not found, see .../Suggested-Tags |
| `$vref` ksp-avc but no `.version` / `.version` present but no `$vref` | warning | $vref is ksp-avc, version file missing / $vref is not ksp-avc, version file present: X |
| MM syntax in cfgs but no ModuleManager depends (or the reverse) | warning | ModuleManager syntax used without ModuleManager dependency / dependency may not be needed |
| no DLL named like the identifier | warning | No plugin matching the identifier, manual installations won't be detected: ... |
| plugin mod with unbounded future compatibility | warning | Unbounded future compatibility for module with a plugin, consider setting $vref or ksp_version or ksp_version_max |
| C# sources but no DLL | warning | Found C# source code without DLL, mod may not have been compiled |
| craft files outside Ships/, Missions/, GameData/ContractPacks/ | warning | Craft files installed outside Ships folder (see note below - not always a fix) |
| `include_only` matched nothing | warning | No matches for include_only |
| swinfo.json present/absent vs `$vref` space-warp | warning | ... |
| empty PR body | warning | Pull requests should have a description |

## CI-CRAFT: Interpret the craft-location warning before fixing it

A craft outside Ships is not necessarily misplaced. Determine its purpose:

| Craft purpose | Correct treatment |
| --- | --- |
| Player loads it in the VAB/SPH and launches it | Install under `Ships/VAB` or `Ships/SPH`. `CST100Starliner.netkan` is an example. |
| Contract or mission prop, such as a wreck or rescue target | Keep the GameData path referenced by the CFG. Treat the warning as expected for this file. |

Search the ZIP's CFGs for the craft filename and `craftURL`. Contract
Configurator's `SpawnVessel`, for example, resolves
`craftURL = GAPFAS/Assets/Ships/MissingAircraft.craft` relative to GameData.
Moving that file to Ships breaks the reference and exposes a prop as a launchable
ship. See INSTALL-CONTENT and the [install reference](spec-cheatsheet.md#install).

## CI-LIMITS: What the reviewer must establish

CI can catch some failures in each area without proving the overall decision:

| Area | What still needs review |
| --- | --- |
| Identifier | Core name, stable folder/DLL match, duplicates, and case collisions. CI checks syntax and filename equality. |
| License | Agreement with LICENSE, README, or forum evidence. CI validates the license value, not permission or licensing accuracy. |
| Tags | Correct Suggested Tags. CI warns on absence, not suitability. |
| Relationships | Exact targets and complete requirements. A nonexistent `depends` can fail the sandbox install; wrong optional relationship names can pass. MM detection does not find every missing dependency. |
| Bundles | Exclude bundled mods and declare relationships. CI catches only collisions encountered by its sandbox. |
| Install selection | Intended folders, missing siblings, extras, sources, craft purpose, and paths stable across releases. An empty `find` or unmatched selection can fail CI, but a successful selection can still be wrong. |
| Display fields | Useful name/abstract and correct forum homepage. |
| Versions | Appropriate version scheme and future tag handling. Different strings across hosts can fail inflation; a successful merge does not prove the scheme is maintainable. |
| Hosts | Usable fallback hosts, appropriate source archives, and unambiguous asset selection. |
| Permission | Author/maintainer consent and opt-out policy. |
| Game | KSP1 rather than a KSP2 payload. SpaceDock `game_id: 3102` identifies KSP1. |
| Embedded metadata | Conflicts with internal `.ckan`, `.version`, or `swinfo.json`. |
| Release history | Other ZIP layouts. CI inflates only its latest release. |
| Metanetkans | Correctness of the remote file beyond its ability to inflate. |

## CI-LOGS: Find the useful evidence

```bash
gh pr checks <N> -R KSP-CKAN/NetKAN
gh run view --job <JOB_ID> -R KSP-CKAN/NetKAN --log
gh run download <RUN_ID> -R KSP-CKAN/NetKAN -n metadata-<N> -D <dir>
```

The check link contains the job ID. Within the log:

| Group or line | Evidence |
| --- | --- |
| `Inflating NetKAN/<id>.netkan` | Validator annotations and generated `.ckan` |
| `Diffing ...` | Changes relative to existing metadata |
| `Installing <name> <version>` | Sandbox install result |
| `About to install:` | Dependency resolution |
| `Showing N installed files:` | Actual installed file list |
| `Version  Game Versions` table | Compatibility |

If the check is absent, use local inflation. First-time contributors may need a
maintainer to select "Approve and run"; state that CI is pending. For queued
checks and infrastructure failures, see [Uncommon cases](uncommon-cases.md#fallback-ci-missing-or-unusable-ci).
