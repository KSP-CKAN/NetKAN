# What the NetKAN CI ("Inflate netkans" check) does and does not catch

## Contents
- What CI runs for a PR (steps, PR-body directives)
- Validator matrix (every error and warning message)
- What CI does NOT check
- Reading the CI log quickly (commands, log groups)

Source: `.github/workflows/inflate.yml` in the NetKAN repo, the `KSP-CKAN/xKAN-meta_testing`
action (`ckan_meta_tester.py`), and the validators in `KSP-CKAN/CKAN/Netkan/Validators/*.cs`.

## What CI runs for a PR

1. `yamllint` (relaxed) on every `.netkan` added/modified between the merge-base and HEAD.
   New `.netkan` files must live in `NetKAN/`; a `.frozen` twin must not exist.
2. `netkan.exe --game KSP --highest-version <from CKAN-meta> <file>`: inflates the LATEST release
   only, running the NetKAN validators (below). Output ends up in the log group
   `Inflating NetKAN/<id>.netkan`, followed by the generated `.ckan` JSON. "Latest" means the
   release that was newest when the PR was last pushed: CI does not re-run when the author
   publishes a new release, so a green check can describe a ZIP that no longer exists upstream
   (facts.md's "Coverage" line and local inflation show the current one).
   Validators run once per host document, so a two-host netkan prints the same warning twice
   (facts.md collapses these to one line with `x2`); count it as one finding.
3. If CKAN-meta already has a `.ckan` for that identifier+version, a `Diffing <name> <version>`
   group shows what changed (empty diff -> install step skipped).
4. `Installing <name> <version>` group: installs the module plus its dependencies into a dummy
   game instance using the newest compatible game version, then runs `ckan show`, which prints
   `Showing N installed files:` (the authoritative list of what users will get) and the
   compatibility table. Failure here (unresolvable dependency, conflict, file collision) fails CI.
5. Uploads the inflated `.ckan`s as artifact `metadata-<PR>`.

PR-body directives the tester honours (put them in the PR description):
- `ckan compat add 1.10 1.11 1.12`: pretend those game versions are compatible so dependencies
  with narrower compatibility can be installed in the sandbox.
- `ckan install ModA ModB=1.2`: extra install tests after the main one.
- `#overwrite_cache`: re-download the mod if the author replaced the release file.
- An empty PR body produces a warning on every file.

Warnings/errors appear as GitHub annotations (`##[warning]`, `##[error]`) at the top of the
job log and on the PR "Files" tab. Only `ERROR`/`FATAL` lines fail the job.

## Validator matrix

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

**"Craft files installed outside Ships folder" is not always a bug.** A `.craft` file bundled
inside the mod's own `GameData/<Id>/...` can be a contract/mission prop, not a player-launchable
ship: Contract Configurator's `SpawnVessel` behaviour (and similar wreck/rescue spawners) loads it
via a `craftURL` that is a GameData-relative path baked into the `.cfg` (e.g. `craftURL =
GAPFAS/Assets/Ships/MissingAircraft.craft`). Moving that file to `Ships/SPH` or `Ships/VAB` to
silence the warning breaks the contract (the hardcoded `craftURL` no longer resolves) and also
wrongly hands the player a "ship" in the editor that was never meant to be launched. Before
"fixing" this warning, grep the ZIP's `.cfg` files for the craft's filename/`craftURL`; if a
contract behaviour references it by its GameData path, leave it installed there and treat the
warning as expected noise for this file. Only relocate to `Ships/...` when the craft is genuinely
meant for the player to load in the VAB/SPH craft list (see `CST100Starliner.netkan` for that
case, and the spec cheat-sheet's `install` section).

## What CI does NOT check (a reviewer must)

- Whether the identifier is *good* (core name only, matches the GameData folder or DLL, not a
  duplicate of an already-indexed mod under a different identifier, not case-colliding).
- Whether `license` matches the ZIP's LICENSE file / forum thread (only that it is a valid string).
- Whether tags are the right ones from the Suggested Tags list (only that some exist).
- Whether relationship targets exist and are the right identifiers. CI installs `depends` in the
  sandbox, so a non-existent `depends` fails the install step, but wrong `recommends`, `suggests`,
  `supports`, `conflicts` names pass silently. Missing dependencies (other than MM syntax) pass.
- Whether a bundled third-party mod is being installed (only file collisions with the sandbox
  install are caught, and dependencies are only installed if declared).
- Whether the install stanza installs the RIGHT subset: extra folders (source, docs, Ships,
  craft files, optional patches, "Extras"), missing sibling folders, `find: ''`, or a `file:`
  path that breaks on the next release.
- Whether `homepage` points at the forum thread; whether `name`/`abstract` are sane.
- Whether the version string is sane (`v` prefix, dates, spaces) and consistent between hosts.
- Whether a GitHub-hosted mod should also/instead be indexed from GitHub (multi-hosting), whether
  `use_source_archive` is right, whether `asset_match` is needed (several zips per release).
- Whether the uploader/PR author is the mod author or has permission; opt-out list.
- Whether the mod is KSP1 at all (KSP2 mods go to KSP2-NetKAN; SpaceDock `game_id` 3102 = KSP1).
- Whether a `.ckan`, `.version` or `swinfo.json` inside the ZIP contains metadata that conflicts
  with the netkan.
- Older releases: CI inflates only the latest release; previous releases may have a different
  layout.
- Anything about a metanetkan's remote file beyond it inflating successfully.

## Reading the CI log quickly

```
gh pr checks <N> -R KSP-CKAN/NetKAN                       # state + link (job id is in the link)
gh run view --job <JOB_ID> -R KSP-CKAN/NetKAN --log        # full log
gh run download <RUN_ID> -R KSP-CKAN/NetKAN -n metadata-<N> -D <dir>   # inflated .ckan artifact
```
Key groups: `Inflating NetKAN/<id>.netkan` (annotations + generated .ckan), `Diffing ...`,
`Installing <name> <version>` (`About to install:` = dependency resolution; `Showing N installed
files:` = final file list; the `Version  Game Versions` table = compatibility).

If there is no check at all, the workflow has not run: first-time contributors need a maintainer
to click "Approve and run". Inflate locally instead (`netkan.exe`), or ask for approval.
