# Evaluation cases

Real PRs used to check that the skill produces the right findings. Re-run with
`python scripts/netkan_pr_diag.py <N>` and compare the report against the expected behaviour.
(PR state changes over time; expectations describe the PR as of 2026-09-04.)

## Case 1: SpaceDock bot PR, multi-host, CI failure (PR #11494, KerbalAdvancedDefenseReborn)
Expected behaviour:
- Verdict NEEDS CORRECTIONS; CI FAILURE quoted: "Generated 2 modules but only 1 requested:
  0.3.5 on github.com; V0.3.5 on spacedock.info".
- BLOCKER: `x_netkan_version_edit: ^V?(?<version>.+)$` must also be in the SpaceDock document.
- SHOULD-FIX: `$vref: '#/ckan/ksp-avc'` in both documents (ZIP ships `KerbalAdvancedDefenseReborn.version`; CI warns).
- SHOULD-FIX: missing `depends: BDArmory` (SpaceDock description "Dependencies: BDArmory Plus";
  `BDArmory` is provided by `BDArmoryContinued`; 8 precedent netkans use `depends: BDArmory`).
- Judgement call: `suggests: KerbalChangelog` (changelog.cfg) and `supports`/`suggests: VABOrganizer`
  (Patches/KAD_VABOrganizer.cfg); `combat` tag alongside `parts`.
- Checked OK: identifier matches the GameData folder (default install works despite the
  `Kerbal-Advanced-Defense-Reborn-main` wrapper folder), MIT on GitHub and SpaceDock, not a duplicate,
  KSP1, uploader Iftn = GitHub owner Iftn1.

## Case 2: SpaceDock bot PR, invalid license, no inflation (PR #11508, SpaceProbesSharp)
Expected behaviour:
- Verdict NEEDS CORRECTIONS; CI FAILURE "The licence MIT-(configs)/ARR-(assets) is invalid".
- BLOCKER: set `license: restricted` (mixed MIT/ARR -> most restrictive) in the netkan.
- ZIP inspected via the host fallback: root folder `SpaceProbesSharp` matches identifier (default
  install OK), no DLL, no `.version`, Waterfall + ModuleManager deps confirmed by cfg contents.
- SHOULD-FIX/judgement: `recommends`/`suggests: BluedogDB` ("Highly Recommended: BDB") - check the
  identifier `Bluedog-Design-Bureau`/`BluedogDB` in NetKAN before naming it.
- Tags: `parts`, drop `graphics` unless the pack is primarily visual (Waterfall plumes only).

## Case 3: Human PR, CI not run, legacy folder name (PR #11485, HeatTilePainter)
Expected behaviour:
- Verdict LOOKS CORRECT (CI pending) or NEEDS CORRECTIONS depending on judgement; CI "not run".
- Local inflation succeeds with WARN "No plugin matching the identifier ... HeatTileOverlayPrototype.dll".
- Judgement call reported: identifier `HeatTilePainter` vs folder/DLL `HeatTileOverlayPrototype`
  (author explains the legacy name is kept for craft compatibility); options: keep identifier +
  explicit `find`, or rename identifier to `HeatTileOverlayPrototype`.
- NICE-TO-HAVE: `asset_match` regex is fine but unnecessary while the release has one ZIP; the
  `.sha256` asset is ignored. `x_netkan_version_edit` applied to tag `v0.24.1` -> `0.24.1`.
- Checked OK: MIT in LICENSE.txt and GitHub, forum thread homepage, ModuleManager dep justified
  by MM syntax in the cfg, `$vref` with a valid `.version`, tags plausible.

## Case 4: Bot PR installing into another mod's folder (PR #11504, RealisticTUFXbyGeminiAI)
Expected behaviour:
- Verdict NEEDS CORRECTIONS (or READY with judgement), CI SUCCESS.
- Finding: `find: TUFX` -> installs `GameData/TUFX/Profiles/RealGeminiTUFX.cfg` inside the TUFX
  mod's folder. Report as a judgement call with precedents (other TUFX profile packs use
  `file: <profile>.cfg` with `install_to: GameData/<OwnFolder>` or `find: <own folder>`); suggest
  `install: [{file: GameData/TUFX/Profiles/RealGeminiTUFX.cfg, install_to: GameData/TUFX/Profiles}]`
  only if that is what precedents do, else keep and flag.
- Identifier `RealisticTUFXbyGeminiAI` contains the author/tool name; SHOULD-FIX to shorten
  (e.g. `RealisticTUFX`) is a judgement call because the SpaceDock title is the mod's name.
- License CC0 from SpaceDock is valid; empty homepage is acceptable (no forum thread known).

## Case 5: Metanetkan PR (PR #11509, BoundlessMissions)
Expected behaviour:
- Reviews the REMOTE netkan content; reports the `v1.0.0` version string (needs
  `x_netkan_version_edit: ^v?(?<version>.+)$` in the remote file), the WARN about DLL names
  (`GeneKerman.dll`, `websocket-sharp.dll` vs identifier), and the reviewer's suggestion to use an
  internal `.ckan` instead of a metanetkan as a judgement call.

## Case 6: Human duplicate of a bot PR, latest release broke after CI (PR #11500, KerbalAdvancedDefenseReborn)
Run by a Sonnet agent on 2026-09-04 (report validated). Expected behaviour:
- Verdict `BLOCKED: duplicate of open PR #11494` (gatekeeping rule wins even though metadata
  fixes are also listed); CI SUCCESS on V0.3, but facts.md must show the Coverage WARNING and a
  `LATEST UPSTREAM RELEASE V0.3.5` entry, and local inflation FATAL
  "No files found matching find="GameData" to install!".
- BLOCKER: `install: [{find: GameData}]` matches nothing in V0.3.5 (ZIP root is
  `Kerbal-Advanced-Defense-Reborn-main/KerbalAdvancedDefenseReborn/`, no GameData folder; both
  hosts byte-identical). Fix: delete the `install` block (identifier == mod folder in both layouts).
- SHOULD-FIX: `$vref` only on the SpaceDock document; V0.3.5 ships a valid `.version`.
- NICE-TO-HAVE / judgement: `suggests: VABOrganizer` (`:NEEDS[VABOrganizer]` patch, precedent
  KerbalPowersArmory), `suggests: KerbalChangelog` (changelog.cfg in V0.3.5).
- Must NOT ask for `x_netkan_version_edit`: GitHub tags and SpaceDock versions both read
  `V0.3.5`, and a shared prefix is not a problem (wrangler feedback 2026-09-04).
- Permission: PR body has no link, but the forum thread (read via the Chrome JS snippet) has the
  author thanking the PR author for modeling help and announcing CKAN availability -> Checked OK,
  ask for the link as a judgement-call item, not BLOCKED.
- Must NOT copy facts from reference/example-report.md (#11494 uses `depends: BDArmory`; this PR
  uses `BDArmoryForRunwayProject`, which is also fine).
