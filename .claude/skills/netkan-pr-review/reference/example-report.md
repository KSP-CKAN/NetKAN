# Example report: PR #11494 on 2026-09-04

Use this example for report structure and evidence depth. It is a historical
snapshot, not a source of facts for another review. The same mod was submitted
again as PR #11500 with different content, and upstream releases changed.

When editing the example, keep evidence, correction, and proposed YAML together.
Maintain the report headings required by [SKILL.md](../SKILL.md). For a new PR,
replace every factual statement with evidence gathered for that PR.

The sample illustrates three corrections: inconsistent host versions, missing
`$vref`, and a missing framework dependency. It also shows optional decisions
separately from required fixes.

---

# NetKAN PR #11494: Add Kerbal Advanced Defense Reborn from SpaceDock
https://github.com/KSP-CKAN/NetKAN/pull/11494
**Verdict:** NEEDS CORRECTIONS
**CI:** FAILURE - `FATAL ... Generated 2 modules but only 1 requested: 0.3 on github.com; V0.3 on spacedock.info`. Local inflation reproduces the mismatch for V0.3.5.
**Mod:** Kerbal Advanced Defense Reborn by Iftn; hosts spacedock/4522 + github Iftn1/Kerbal-Advanced-Defense-Reborn; latest V0.3.5 (2026-08-31); license MIT on both hosts; PR by netkan-bot (bot)
**Works?** plausible (static check only, 3k)

## Corrections needed

1. **[BLOCKER] Different version strings across hosts.** GitHub strips the `V`
   prefix; SpaceDock keeps it, so the release inflates as both `0.3.5` and
   `V0.3.5` and cannot merge.

   **Evidence:** CI annotation above; SpaceDock `friendly_version: "V0.3.5"`;
   `version_edit_applied` confirms GitHub tags `V0.1` through `V0.3.5` match.

   **Fix:** apply the same edit to the SpaceDock document:

   ```yaml
   identifier: KerbalAdvancedDefenseReborn
   $kref: '#/ckan/spacedock/4522'
   x_netkan_version_edit: ^V?(?<version>.+)$
   ```

2. **[SHOULD-FIX] Installed version file has no `$vref`.** Both documents need
   the reference to this mod's version file.

   **Evidence:** both hosts warn `$vref is not ksp-avc, version file present:
   .../KerbalAdvancedDefenseReborn/KerbalAdvancedDefenseReborn.version`. The JSON
   has VERSION 0.3.5, KSP_VERSION_MIN 1.12.5, KSP_VERSION_MAX 1.12.99, a URL,
   and a matching NAME.

   **Fix:** add this to both documents:

   ```yaml
   $vref: '#/ckan/ksp-avc'
   ```

3. **[SHOULD-FIX] Required BDArmory relationship is missing.** These missile
   parts have no purpose without BDArmory.

   **Evidence:** SpaceDock and README say "Dependencies: BDArmory Plus".
   `BDArmoryContinued.netkan` provides the virtual identifier with
   `provides: [BDArmory]`; eight existing weapon packs depend on that identifier.

   **Fix:** update the SpaceDock document's dependencies:

   ```yaml
   depends:
     - name: ModuleManager
     - name: BDArmory
   ```

   Keep ModuleManager: `Patches/KAD_VABOrganizer.cfg` uses its patch syntax.

## Judgement calls / questions for the author

- **Changelog integration:** `changelog.cfg` contains `KERBALCHANGELOG`.
  Consider `suggests: - name: KerbalChangelog`; 15 of 23 referencing netkans
  used suggests in the sample.
- **VABOrganizer:** `Patches/KAD_VABOrganizer.cfg` is optional. Precedents
  SillyPhotonDrives and SupplementaryElectricEngines use supports; suggests is
  another option. Choose based on which direction the integration should be offered.
- **Tags:** parts is appropriate; consider the combat descriptor for weapons.
- **Archive wrapper:** GitHub's asset has a
  `Kerbal-Advanced-Defense-Reborn-main/` wrapper. Default
  `find: KerbalAdvancedDefenseReborn` still selects the inner folder; no change
  is needed for this layout.

## Checked and OK

- **Permission:** SpaceDock author Iftn, GitHub owner Iftn1, and `.version`
  GITHUB.USERNAME identify the maintainer; the author's bot request supplies consent.
- **Game:** SpaceDock game_id 3102 and version-file KSP range 1.12.5-1.12.99.
- **Duplicates:** no `KerbalAdvancedDefenseReborn.*` on master; no other entry
  uses SpaceDock 4522 or this repository; no similar identifier. SpaceDock search
  returns only 4522 and the status page has no entry.
- **Install:** identifier matches the GameData folder in both ZIPs. The same
  95 files are present on both hosts; default install is sufficient. No DLLs,
  so plugin-name detection does not apply.
- **License:** MIT in GitHub LICENSE, SpaceDock, and `changelog.cfg`. The ZIP
  has no separate license file; the agreeing host evidence is acceptable here.
- **Homepage:** SpaceDock website and GitHub homepage both point to the forum.
- **Function:** installed part CFGs have models and textures; MM patches target
  BDArmory, which is included in the proposed dependencies. Static inspection only.
- **Extras:** no bundled third-party mods, junk, or craft files.
- **Version edit:** matches all four recorded tags, from `V0.1` to `V0.3.5`,
  producing versions `0.1` to `0.3.5`.

## Facts

- facts: `<tmp>/netkan-pr-review/pr-11494/facts.md`
- CI: https://github.com/KSP-CKAN/NetKAN/actions/runs/33251768335/job/99098550941
- ZIP listing: `<tmp>/netkan-pr-review/pr-11494/ziplist-KerbalAdvancedDefenseReborn-UNINFLATED-doc0.txt`

**Proposed netkan:** applies corrections 1-3 and the optional KerbalChangelog
suggestion. This is a proposal, not an edit to the submission.

```yaml
identifier: KerbalAdvancedDefenseReborn
$kref: '#/ckan/github/Iftn1/Kerbal-Advanced-Defense-Reborn'
$vref: '#/ckan/ksp-avc'
x_netkan_version_edit: ^V?(?<version>.+)$
---
identifier: KerbalAdvancedDefenseReborn
$kref: '#/ckan/spacedock/4522'
$vref: '#/ckan/ksp-avc'
x_netkan_version_edit: ^V?(?<version>.+)$
tags:
  - parts
  - combat
depends:
  - name: ModuleManager
  - name: BDArmory
suggests:
  - name: KerbalChangelog
x_via: Automated SpaceDock CKAN submission
```
