# Example report (PR #11494 as of 2026-09-04)

Produced from `facts.md` for a SpaceDock bot PR with a GitHub + SpaceDock document. Shows the
expected level of detail: every correction quotes its evidence and gives the replacement.

**Use this for structure and depth only.** Its facts were true for PR #11494 on 2026-09-04 and
for no other PR (the same mod has since been re-submitted by a human as #11500 with different
content, and its releases have changed). Every statement in your own report must come from your
own `facts.md`.

---

# NetKAN PR #11494: Add Kerbal Advanced Defense Reborn from SpaceDock
https://github.com/KSP-CKAN/NetKAN/pull/11494
**Verdict:** NEEDS CORRECTIONS
**CI:** FAILURE - `FATAL ... Generated 2 modules but only 1 requested: 0.3 on github.com; V0.3 on spacedock.info` (local inflation reproduces it for V0.3.5)
**Mod:** Kerbal Advanced Defense Reborn by Iftn; hosts spacedock/4522 + github Iftn1/Kerbal-Advanced-Defense-Reborn; latest V0.3.5 (2026-08-31); license MIT (GitHub and SpaceDock agree); PR by netkan-bot (bot)
**Works?** plausible (static check only, 3k)

## Corrections needed
1. **[BLOCKER] version string differs between hosts:** the GitHub document strips the `V` prefix (`x_netkan_version_edit: ^V?(?<version>.+)$`) but the SpaceDock document does not, so the same release inflates as `0.3.5` and `V0.3.5` and the two downloads cannot merge. Evidence: CI annotation above; SpaceDock API `friendly_version: "V0.3.5"`; GitHub tags `V0.1`..`V0.3.5` all match the regex (`version_edit_applied`). Fix: add the same line to the SpaceDock document:
   ```yaml
   identifier: KerbalAdvancedDefenseReborn
   $kref: '#/ckan/spacedock/4522'
   x_netkan_version_edit: ^V?(?<version>.+)$
   ```
2. **[SHOULD-FIX] `$vref` missing although the ZIP ships a `.version` file:** both hosts warn `$vref is not ksp-avc, version file present: .../KerbalAdvancedDefenseReborn/KerbalAdvancedDefenseReborn.version`. The file is valid (`VERSION 0.3.5`, `KSP_VERSION_MIN 1.12.5`, `KSP_VERSION_MAX 1.12.99`, `URL` set, `NAME` matches). Fix: add to BOTH documents:
   ```yaml
   $vref: '#/ckan/ksp-avc'
   ```
3. **[SHOULD-FIX] missing dependency on BDArmory:** the SpaceDock description and README say "Dependencies: BDArmory Plus"; the parts are missiles for BDArmory and do nothing without it. In `NetKAN/`, `BDArmory` is a virtual identifier provided by `BDArmoryContinued` (`BDArmoryContinued.netkan: provides: [BDArmory]`) and eight existing weapon packs use `depends: - name: BDArmory`. Fix (SpaceDock document):
   ```yaml
   depends:
     - name: ModuleManager
     - name: BDArmory
   ```
   `ModuleManager` stays: `Patches/KAD_VABOrganizer.cfg` uses MM syntax.

## Judgement calls / questions for the author
- `changelog.cfg` is a `KERBALCHANGELOG` node: add `suggests: - name: KerbalChangelog` (house style, 15 of 23 netkans that reference it use `suggests`).
- `Patches/KAD_VABOrganizer.cfg` is an optional VABOrganizer patch: precedents use `supports: - name: VABOrganizer` (SillyPhotonDrives, SupplementaryElectricEngines) or `suggests`; pick one.
- Tags: `parts` is right; consider adding `combat` (Suggested Tags descriptor for weapons packs).
- The GitHub release asset is a repository snapshot with a wrapper folder `Kerbal-Advanced-Defense-Reborn-main/`; the default install still works because `find: KerbalAdvancedDefenseReborn` matches the inner folder. No change needed unless the author repackages.

## Checked and OK
- Permission: SpaceDock author `Iftn` = GitHub owner `Iftn1` = `.version` `GITHUB.USERNAME`; bot PR counts as consent.
- KSP1: SpaceDock game_id 3102; `.version` KSP 1.12.5-1.12.99.
- Not a duplicate: no `KerbalAdvancedDefenseReborn.*` on master, no other netkan uses spacedock/4522 or this repo, no similar identifiers; SpaceDock search returns only id 4522; not on the status page.
- Identifier = GameData folder `KerbalAdvancedDefenseReborn` in both ZIPs (95 files, identical on both hosts); no `install` block needed; no DLLs, so no plugin-name warning.
- License MIT on GitHub (`LICENSE`), SpaceDock, and `changelog.cfg`; no license file inside the ZIP (acceptable, hosts agree).
- Homepage: SpaceDock `website` is the forum thread; GitHub `homepage` is the same URL.
- Could it work: the 95 installed files include the part `.cfg`s with their `.mu` models and textures; no DLL to check; MM patches target BDArmory, which is being added as a dependency (static check only).
- No bundled third-party mods; no junk files; no craft files.
- Version-edit regex matches all four existing tags (`V0.1`..`V0.3.5` -> `0.1`..`0.3.5`).

## Facts
- facts: `<tmp>/netkan-pr-review/pr-11494/facts.md`; CI: https://github.com/KSP-CKAN/NetKAN/actions/runs/33251768335/job/99098550941; ZIP listing: `<tmp>/netkan-pr-review/pr-11494/ziplist-KerbalAdvancedDefenseReborn-UNINFLATED-doc0.txt`

Proposed netkan (proposal, applying 1-3 and the KerbalChangelog suggestion):
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
