# Historical NetKAN review findings, 2024-2026

Use this reference for historical examples, reviewer feedback, and relative frequency.
These observations explain the checks; they do not override the current [Review
rules](review-rules.md) or verdicts in [SKILL.md](../SKILL.md).

## Maintaining this reference

Keep findings under their existing labels, grouped by area. Each entry separates its
sample count/severity, review guidance, and supporting evidence. Historical severity and
CI coverage describe the sample rather than defining current policy. Add examples to the
relevant entry instead of appending competing rules.

The original source used META-04 for both relationship typos and display-name
corrections. Those labels are retained here; use the descriptive title to tell them
apart.

## Contents

- [Sample and interpretation](#sample-and-interpretation)
- [Frequency of fixes](#frequency-of-fixes)
- [Dependencies](#dependencies)
- [Optional relationships and conflicts](#relationships-other-than-depends)
- [Install selection and ZIP contents](#install-stanza-and-zip-contents)
- [Identifiers](#identifier)
- [Duplicates and frozen entries](#duplicates-and-frozen-entries)
- [Hosting and versions](#hosting-and-version-strings)
- [Compatibility](#compatibility)
- [Licenses](#license)
- [Tags](#tags)
- [Display fields and resources](#name-abstract-author-resources)
- [File format](#file-format)
- [Permission policy](#policy)
- [Additional patterns](#additional-patterns-from-the-completeness-pass)
- [Tooling limits](#tooling-limits-in-the-sampled-environment)
- [Bot patterns](#bot-patterns-illustrated-by-the-sample)
- [Closure reasons](#closure-reasons-recorded-in-the-24-unmerged-prs)

## Sample and interpretation

The sample contains 112 PRs: 32 SpaceDock-bot Add submissions, 32 human Add submissions,
12 labelled Fix install/license/relationships, 12 other merged PRs, and 24 closed
without merge. It also includes all 34 direct-to-master commits fixing an entry within
60 days of its addition (post-merge review misses).

Each first-submitted file was compared with its merged state, every reviewer comment was
read, and the findings were rechecked against the dossiers. Counts are distinct sampled
PRs/commits; treat them as relative weights.

## Frequency of fixes

The sample records 331 fixes. In the bot-PR sample, none of the recorded corrections was
flagged by CI. This does not mean bot submissions cannot fail CI: the corrections
required ZIP, host, forum, or repository evidence.

| Category | Fixes | Caught by CI | Typical trigger |
|---|---|---|---|
| Missing `depends` | 46 | 2 | cfg `:NEEDS`/`:FOR`, README "requires", SpaceDock description, sibling mods |
| `install` stanza wrong/redundant | 34 | 18 (mostly "matches nothing") | ZIP layout vs `find` |
| `recommends`/`suggests`/`supports` | 34 | 2 | description, forum thread, semantics of `supports` |
| `name`/`abstract`/`author` | 29 | 2 | hard-coded copies of host data, typos, missing co-authors |
| Tags | 21 | 1 | bot structural tags vs Suggested Tags |
| File format / YAML | 20 | 4 | JSON->YAML, missing colon, quoting, mixed syntax |
| `$kref` / hosting | 17 | 4 | missing second host, renamed repo, no release asset |
| License | 16 | 3 | invalid string, wrong variant, mixed licensing |
| Duplicate / frozen | 16 | 2 | same mod already indexed under another identifier |
| Identifier | 16 | 3 | bot title-derived identifier, folder/DLL mismatch |
| Version string | 13 | 8 | `v` prefix on one host only, regex too strict |
| `resources.homepage` | 10 | 0 | forum thread missing, GitHub URL instead |
| `conflicts`/`provides`/`replaced_by` | 9 | 2 | forks, virtual packages, incompatibilities |
| `$vref` | 8 | 2 | `.version` present but no `$vref`, or only on one host |
| Module split / bundling | 8 | 1 | two mods in one ZIP, optional folders, bundled deps |

## Findings by area

Historical blocker meant held or closed; should-fix meant normally corrected before
merge; nice-to-have meant corrected when noticed, sometimes after merge. Use the skill's
current severity rules for a new review.

### Dependencies

#### DEPS-01 Missing transitive / companion / library dependency

**Historical sample:** 32 sources, should-fix, CI: no.

Do not rely on bot detection for all requirements. Check the parent mod being extended,
shared libraries (`Harmony2`, `ToolbarController`, `ClickThroughBlocker`,
`SpaceTuxLibrary`, `HUDReplacer`, `TextureReplacer`, `FireflyAPI`, `KSPCommunityFixes`),
resource packs (`CommunityResourcePack`), or Kopernicus expansion components
(`VertexHeightOblateAdvanced`, `VertexColorMapEmissive`,
`VertexMitchellNetravaliHeightMap`, `ScaledDecorator`, `Singularity`,
`KopernicusExpansionContinueder`, `ModularFlightIntegrator`).

**Check:** inspect these sources before declaring a requirement:

- CFG `:NEEDS[...]`, `:FOR[...]`, `:AFTER[...]`, non-stock RESOURCE names,
  and MODULE names such as `ModuleB9PartSwitch`, `ModuleWaterfallFX`,
  `ModuleRestockDepthMask`, `Scatterer_*`, `EVE_*`, `TUFX_PROFILE`, and
  `KERBALCHANGELOG`.
- SpaceDock requirements, GitHub README, forum thread, and sibling mods.
- DLL references such as `0Harmony`, `ToolbarControl`, and `ClickThroughBlocker`.

When available, use ilspy `get_assembly_attributes` and
`list_assembly_references` on each plugin DLL. Look for
`KSPAssemblyDependency` attributes and referenced mod assemblies. A reference on
the main DLL (matching the identifier/GameData folder) supports `depends`.
A reference confined to an optional bridge DLL supports `suggests` instead;
it does not make the companion mandatory for the whole mod.

**Reviewer feedback:** "Don't forget to check the SpaceDock page, this one also had a
new dependency added after the PR was submitted." / "There's also a missing dependency
here. Check the forum thread or SpaceDock." / "Is the dependency on SSPX purely for
HabUtil.dll?"

**Evidence:** #9937 (Singularity + KopernicusExpansion), #9980, #10191
(StationPartsExpansionRedux for a shared DLL), #10326 (BeyondJool +
VertexHeightOblateAdvanced), #10368 (Harmony2, CommunityCategoryKit, VABOrganizer),
 #10505 (B9PartSwitch, ChemicalCore, CRP), #10697 (eight Kopernicus-expansion deps added
at once), #10943, #11024, #10870, #10448.

#### DEPS-02 ModuleManager missing although cfgs use MM syntax

**Historical sample:** 6, should-fix, CI: warning.

CI warns "ModuleManager syntax used without ModuleManager dependency". Confirm it
against the installed CFGs, then add the requirement. Conventionally, ModuleManager is
first in `depends`.

**Evidence:** #10191, #10734, #10787, #11179, 79cbb53c.

#### DEPS-03 Prefer the real dependency over a bundled copy

**Historical sample:** 2, should-fix, CI: no.

When a dependency DLL/folder is bundled, exclude the copy with `filter` and keep the
relationship to the real package. Do not drop the dependency.

**Reviewer feedback (HebaruSan):** "real dependencies should still be preferred over
bundling when possible. Let's filter out the bundled mod instead."

**Evidence:** #10718 (`filter: ScaledDecorator`).

**Historical exception:** a reviewer may suggest bundling a small shared DLL when the
dependency mod is huge (#10191), so raise it as a judgement call.

#### REL-03: Optional integrations that create resolver cycles

**Historical sample:** 2, should-fix.

Circular recommendation/dependency chains can fail sandbox installs. Optional
integrations belong in `suggests` (Debian sense: "consider also installing"), reserving
`recommends` for one the resolver should install by default. Do not soften a
genuinely required dependency merely to make CI pass.

**Evidence:** #9896, #10226.

#### PROC-02 Dependency that cannot be indexed

**Historical sample:** 3, blocker.

A required mod that is paid/Patreon-gated, or deliberately not indexed, makes the PR
unmergeable: close or label `Blocked-on-dependency`.

**Reviewer feedback:** "This depends on a paid mod not in CKAN."

**Evidence:** #10448, #10736, #10826.

#### DEPS-04 Dependency identifier is `.frozen`

**Historical sample:** not a blocker, no fix needed.

This differs from PROC-02. A frozen mod was already indexed. Freezing stops
future inflation, while CKAN-meta continues serving the last indexed version.
A new mod can still depend on it.

Do not propose unfreezing (`git mv Foo.frozen Foo.netkan`) as a correction.
Note it under judgement calls for visibility. Investigate the freeze reason:
inactivity alone is acceptable, but a removed host listing/repository or an
author's abandonment announcement needs attention under PROC-02/DUP-02. Do not
assume the reason from the filename.

**Reviewer correction** (PR #11416, `VertexMitchellNetravaliHeightMap` frozen by the
bulk "Freeze idle mods" sweep but still live upstream): "Frozen dependencies are not a
blocker. We don't need to unfreeze them... Frozen mods are a sign that this warrants
more attention, but depending on a frozen mod is not actually an issue."

### Relationships other than depends

#### REL-01 Missing `recommends`/`suggests` for companion mods

**Historical sample:** 16, nice-to-have, CI: no.

Planet packs -> `Scatterer`, `EnvironmentalVisualEnhancements`, `Firefly`,
`KopernicusExpansion`, `Singularity`, `CustomAsteroids`; parts packs -> `PatchManager`,
`CryoTanks`, CRP, B9PS-based switchers; tools -> `KerbalChangelog`. Source: SpaceDock
description, README, forum thread, what similar mods declare. Default to `suggests` for
these (Debian sense: optional, worth considering); use `recommends` only when the mod is
not normally installed without the companion (e.g. it looks broken or incomplete without
it).

**Evidence:** #10113, #10191, #10280, #10604, #10967, #10669, #10787.

#### REL-02 `supports` used backwards

**Historical sample:** 2, should-fix, CI: no.

`supports: X` means "offer THIS mod when X is installed" (the reverse of `suggests`).
Authors use it as "works with X"; rewrite as `suggests`.

**Evidence:** #10837 (`supports -> suggests`).

#### CPR-01 Missing `conflicts` for a real incompatibility

**Historical sample:** 3, should-fix, CI: no.

Same-folder installs, mods that fix the bug this mod exploits
(PersistentRotationUpgraded vs KSPCommunityFixes), fork vs original. Sources: upstream
issues, forum thread, cross-check section "other netkans referencing" and similar
identifiers.

**Evidence:** #10409, 74cb4266, #10787, #11489.

#### CPR-03 Missing `provides` for interchangeable content

**Historical sample:** 3, should-fix, CI: no.

Sunflare/config packs (`Scatterer-sunflare`, `Scatterer-config`), planet-texture packs
(`ParallaxContinued-Planet-Textures`), renamed mods keep the old identifier in
`provides`. Usually paired with `conflicts` on the same virtual name.

**Evidence:** #10026, #10787, #10477.

#### META-04 Relationship target typos / wrong case

**Historical sample:** 6, should-fix, CI: no.

`VABorganizer` vs `VABOrganizer`, `EnvironmentalVisualEnhhancements`. A wrong name
passes CI and silently never resolves. Check every relationship name against `NetKAN/`
exact-case (the diag script does this).

**Evidence:** 5efc6c04, da552012, #10734.

### Install stanza and ZIP contents

#### INSTALL-02 `find` targets the wrong folder or a version-baked name

**Historical sample:** 13, should-fix, CI: only when nothing matches.

Bot picks an icons-only subfolder, a bundled base mod's folder, the wrapper folder, or
`AutophageMod0.1`. Compare `find` with the ZIP's real payload folder and with the CI
`Showing N installed files` list.

**Evidence:** #9980, #10231, #10326, #10368, #10410, #11166, #10092, #10498, cee18084,
cb241687, d83b05c4.

**Wrapper or namespace?** Choose the fix according to the folder's purpose:

| Folder | Selection |
| --- | --- |
| Unstable wrapper, such as `AutophageMod0.1` or source-archive `<repo>-<sha>/` | Find the stable inner mod folder and install to GameData. |
| Stable author namespace, such as `GameData/AnaAerospace` or `GameData/SterlingSystems` | Find this mod's inner folder and put the namespace in `install_to`. |

Selecting `find: AnaAerospace, install_to: GameData` claims the shared namespace
itself and can conflict with sibling modules. Instead use
`find: RebalancedFuelCost, install_to: GameData/AnaAerospace`: the on-disk layout
is the same, but this module owns only its subfolder.

**Precedent:** the `SterlingSystems*` netkans all do `find: <Module>, install_to:
GameData/SterlingSystems` (e.g. `SterlingSystemsEngines.netkan`: `find: Engines`).

**Evidence:** #11493 (SimpleRebalancedFuelCosts).

#### INSTALL-01 Redundant explicit install stanza

**Historical sample:** 9, nice-to-have but done almost every time.

When the identifier matches the sole GameData folder and default selection is sufficient, delete the `install` block ("Use default install
stanza", "Identifier matches folder name").

**Evidence:** #9937, #10150, #10697, #10776, #11166, #10942, #11143, 6aef8288.

#### INSTALL-03 Optional content needs `filter` or its own module

**Historical sample:** 3, should-fix, CI: no.

`Patches`/`Extras` folders, files shared with a sibling mod (real file-conflict bug in
 #10179), per-file craft stanzas collapsed to one folder stanza (#10008),
runtime-rewritten files filtered so `install_size` stays sane (#10588 `filter:
HETTN.TechTree`).

**Evidence:** #10034, #10179, #10008.

#### SPLIT-01 Two mods (or mutually exclusive variants) in one ZIP need separate netkans

**Historical sample:** 7, should-fix, CI: no.

2D/3D variants, core + optional pack, agency/flags shared between siblings, RP-1
config vs parts. Wire them with `depends`/`suggests`/`conflicts` and `filter` on the
parent.

**Evidence:** #9980, #10470, #11024, #10034, #10179, #10669.

#### SPLIT-02 MM patches must use `:NEEDS[Other]`, never `:FOR[Other]`

**Historical sample:** 1, blocker.

`:FOR[X]` where X is not this mod makes ModuleManager believe X is installed.

**Reviewer feedback (JonnyOThan):** "you must not use `FOR` with an identifier that
isn't your mod."

**Evidence:** #10470.

#### INSTALL-04 Platform-dependent `GameRoot` targets are impossible

**Historical sample:** 1.

`KSP_Data` vs `KSP_x64_Data` cannot be expressed; label `Blocked-on-CKAN-feature`/ask
the author to repackage.

**Evidence:** #10116 (abandoned after 8 months).

#### PROC-03: Malware or bad-faith submissions

**Historical sample:** 2, blocker.

The sample includes a whole-GameData install from a throwaway account with a
vague abstract, closed as "Malware" (#10285), and a hostile trademark-dispute
submission (#10046). Broad installs, absent descriptions, and retaliatory wording
are reasons to inspect the submission. They are not proof of malware by themselves.


### Identifier

#### IDENT-01 Identifier should match the GameData folder or plugin DLL

**Historical sample:** 11, should-fix; CI only errors when identifier != filename.

Apply ID-INSTALL's exception for an author-explained mismatch. When renaming, change
both identifier and filename; INSTALL-01 may then apply.

**Reviewer feedback:** "CKAN can only auto-detect installs if the DLL name matches the
mod's identifier." / "the ckan spec recommends using the same name in the mod's install
directory as the mod's identifier."

**Evidence:** #9937 (`JFAJebFarAway -> JebFarAway`), #10150 (`AtmosphericMinmus ->
MinmusAtmosphere`), #10231 (renamed DLL), #10280 (branding suffix dropped), #10368
(60-char bot identifier trimmed), #10697 (`Almajara-Core`, `Almajara-LastLights` to
match folders), #11097, #11143, #10669, #10080.

#### IDENT-02 Identifier collides with an existing mod's name/brand

**Historical sample:** 3, blocker.

`Kerbcam` vs existing `KerbCam`, `XenonISRU` already used; `Archipelago` renamed
`KSPArchipelago` to avoid the wider project's name. Case-insensitive grep of `NetKAN/`
and a status-page lookup.

**Evidence:** #9908, #11291, #11143.

A SpaceDock page being edited can put UI placeholder text into the generated identifier.
Check that the name is actual mod identity.

### Duplicates and frozen entries

#### DUP-01 Mod already indexed or already has an open PR

**Historical sample:** 12, blocker.

Check `NetKAN/*.netkan` and `*.frozen` for the same SpaceDock id / GitHub repo / folder
name, the open PR list, and recently closed PRs. Reviving a frozen identifier: reuse it
and delete the `.frozen` (#11097 DiscordRP, #10280 Droptank Wrapper unfrozen).

**Reviewer feedback:** "Duplicate of #10460", "There's already a mod called KerbCam (see
 #4031)", "can you please stop opening and closing PRs to add a mod that's already
indexed?"

**Evidence:** #10663, #10428, #11163, #11291, #11446, #10984.

#### DUP-02 Mod removed from its host

**Historical sample:** 2.

SpaceDock listing deleted before merge -> close (#10338, #10949); existing netkans get
frozen when the host listing is gone and the author announced abandonment (#9900,
 #10257).

#### PROC-01 One PR per netkan at a time

**Historical sample:** 2, nice-to-have.

"may I strongly recommend one pull request per netkan at one time?" (#10892); repeated
open/close churn (#10984).

### Hosting and version strings

#### KREF-02 Missing second host (multi-hosting)

**Historical sample:** 4, should-fix, CI: no.

When SpaceDock and GitHub both carry releases, index both (fallback downloads). Verify a
SpaceDock id attached to a sub-module really is that sub-module and not the
parent/sibling.

**Evidence:** #10637, #11016, 810660c1.

#### KREF-01 `$kref` target renamed/removed

**Historical sample:** 6, blocker when it 404s; CI errors on download failure.

Repos get renamed mid-review (#10184), SpaceDock listings get renamed (#10213) or
deleted (#10338, #10949). Open the SpaceDock/GitHub URL from facts.

#### VER-04 GitHub release without assets

**Historical sample:** 1, should-fix, CI: FATAL crash.

"it failed because the ZIP file wasn't attached to the release on GitHub, so I have told
it to only check SpaceDock." Either drop the GitHub document, set `use_source_archive`
if the source archive contains the mod layout and a stable inner-folder `find` selects it, or ask the author to attach the ZIP.

**Evidence:** #10604.

#### VER-05 Multi-asset GitHub release needs `asset_match`

**Historical sample:** 2, should-fix, CI: no unless it picks the wrong one and fails.

Negative look-ahead to exclude a flag pack: `/asset_match/^(?!.*Flagpack)`;
`version_from_asset` to split one release into modules.

**Evidence:** #10942, #10477.

#### VER-01 Version flags not mirrored across host documents

**Historical sample:** 7, should-fix, CI: no.

Check `$vref`, `x_netkan_version_edit`, `x_netkan_force_v`, and required license
overrides in each host document. Missing per-host processing can produce inconsistent
metadata or different version strings. Compare documents side by side and compare the
two inflated `version` values.

**Reviewer feedback:** "Both hosts have v prefix", "need this on both?".

**Evidence:** #10565, #10807 (re-broken by a bot resubmission), #11070, e6249486,
88183e87, e2e916e4, 0dea2625. This was the most common post-merge review miss in the
sample.

#### VER-02 `x_netkan_version_edit` regex too strict for later releases

**Historical sample:** 4, should-fix, CI: no at review time; the bot errors later.

A mandatory space or dot in the regex breaks on the next tag. Prefer
`^v?(?<version>.+)$` or `^[vV]?\.?(?<version>.+)$`; apply the regex to ALL recent tags
(facts: `version_edit_applied`).

**Evidence:** a41a13e7, d78cd3b2, a580eda4, 2560756a.

#### VER-03 Release tag is not a version

**Historical sample:** 1, should-fix.

Tag `stable_release` would become the CKAN version; ask the author to retag (`v1.0`).

**Evidence:** #10877. Also: once a mod has been indexed with a `v` prefix, later hosts
must match (`x_netkan_force_v: true`, 1f32646d CareerReimagined).

### Compatibility

#### GVER-01 Hard-coded `ksp_version*` instead of `$vref`

**Historical sample:** 5, nice-to-have -> should-fix when a `.version` exists.

Remove `ksp_version_min/max` and add `$vref` when the ZIP has a `.version` file
(#10323, #11235, #11016 added `$vref`); collapse min/max to the `ksp_version` shorthand
when a pin is genuinely needed (#11143). Pins are acceptable when there is no `.version`
file and the host gives nothing (#10747 set min 1.8 / max 1.12).

#### VREF: Post-merge version-file misses

`$vref` missing on the GitHub document while present on the SpaceDock one, or missing
altogether though the ZIP ships a `.version` file: 88183e87, e2e916e4, 0dea2625, #11250.
Confirm the CI warning "$vref is not ksp-avc, version file present" against the
installed version file before proposing the correction.

### License

#### LIC-01 License missing, invalid, stale, or unverified

**Historical sample:** 13, should-fix; CI fails only on an invalid string.

SpaceDock free text ("MIT (configs)/ARR (assets)", "CC BY-NC-ND 4.0") -> invalid ->
set a valid value; "All Rights Reserved" -> `restricted`; GitHub auto-detect fails when
there is no machine-readable LICENSE -> set explicitly; a hand-typed value that
duplicates what the host supplies should be removed (7eb28657 "Get KerbalCalculator
license from GitHub"); on multi-host files the license may be needed in the GitHub
document specifically (d84ac784).

**Evidence:** #10842, #10669, cdc46971, 76b59b9a, #11508.

#### LIC-02 Mixed licensing -> single most restrictive value

**Historical sample:** 3, should-fix.

"Most restrictive license takes precedence" (#10787 collapsed `[restricted,
CC-BY-NC-ND]` to `restricted`); art ARR + code CC0 -> `restricted` (#10842).

### Tags

#### TAGS-01 Bot/author tags do not match the Suggested Tags guide

**Historical sample:** 16, should-fix, CI: no.

Drop `config` when `planet-pack`/`parts` already describe the content; drop
`plugin`/`crewed`/ `first-person` that came from a bundled dependency or a stray cfg;
add `physics`, `science`, `graphics`, `app`, `library`, `flags`, `resources`, `crewed`
from the description; reject invented tags (`gameplay`, bc31f731).

**Evidence:** #9895 (+flags), #10113 (-config), #10368, #10776 (+physics), #10877
(config+plugin -> plugin+crewed), #11097 (+app), #11166 (-config +science), #10669.

### Name, abstract, author, resources

#### META-01 Do not hard-code what the host fills in

**Historical sample:** 16, nice-to-have but routinely stripped.

`name` (when equal to the host's), `author`, `license`, `spec_version`,
`resources.homepage/ repository/bugtracker`, `release_status`, `ksp_version_min`.

**Reviewer feedback:** "you can set the homepage link by setting the Website link for
the repo on GitHub; the CKAN bot will pull it into the metadata automatically."

**Evidence:** #10150, #10191, #10323, #10477, #10669, #10747.

#### META-02 Author credit incomplete / bot credited

**Historical sample:** 4, nice-to-have.

Add original authors of continued/redux mods (991f0e4d Coatl, #10604 FuelWings), missing
co-authors (8039f96e), and set `author` explicitly when the host would attribute a bot
account (#9929 "Set author to avoid adding a bot").

#### META-03 / META-04 Name typos and branding

**Historical sample:** 6+3, should-fix.

Hyphenation, missing words ("Institute"), copy-paste variant numbers (8k vs 16k),
trailing whitespace, self-referential abstracts.

**Evidence:** #10184, 30de8b64, c3492a6b, 3da43ce7, #10734.

#### YAML-04 Abstract unreadable

**Historical sample:** 3, nice-to-have.

"After reading this abstract, I did not understand what the mod does." Rewrite from
README; use `>-` folded scalars for long text; keep `description` for detail.

**Evidence:** #10026, #10734, #11143.

#### HOMEPAGE: Forum link

**Historical sample:** 10 fixes.

Forum thread preferred over GitHub URL; empty SpaceDock website -> set
`resources.homepage` explicitly; GitHub-only mods should set the repo Website field
instead.

### File format

#### YAML-01: Syntax mistakes CI may miss

**Historical sample:** 3, blocker.

A missing colon after `depends`/ `supports` can parse as a scalar and silently drop the
whole block (effc85a1 shipped to master with CI green). Inspect the inflated `.ckan` for
missing blocks, not just the parse result.

**Evidence:** #10734, effc85a1.

#### YAML-03 Convert JSON to YAML when touching a file

**Historical sample:** 4 confirmed, nice-to-have.

New files should be YAML; hand-written JSON with errors was abandoned and resubmitted as
`$kref` YAML (#10623 -> #10627).

**Evidence:** #11016, #11143, #11235.

#### XNK-01 `x_via` marker

**Historical sample:** 9, nice-to-have.

Often deleted when a wrangler rewrites the file, but 13+ merged PRs kept it; do not
report it as a correction on its own.

### Policy

#### POLICY-01 Permission for re-uploads, forks, derivatives

**Historical sample:** 3, blocker.

**Reviewer feedback:** "could you please provide some proof that you have permission
from the author to distribute these? We take mod authors' rights seriously" / "CKAN as a
matter of policy only adds mods if the authors agree. Have these authors agreed? If so,
please add a link to where they agreed in the body/description of this pull request for
posterity."

**Evidence:** #9895 (held for a Reddit comment), #10715 (held ~1 month), #10046.

## Additional patterns from the completeness pass

Each appeared two to six times in the raw findings. Use the matching current
rule rather than turning a historical example into a new requirement.

### IDENT-03: Whole marketing titles and scraped UI text

| Submitted identifier | Revised identifier | Source |
| --- | --- | --- |
| `KerbalHacksDroptankWrapperRecolorProjectFelota` | `KerbalHacksDroptankWrapperRecolor` | #10280 |
| `UnmanagedAngerResourcesforKerbalismVABoPrunesCCKConfigToolsPrunes` | `UnmanagedAngerResources` | #10368 |
| `ArcAerospaceWyvernCapsuleRP1Config` | `Wyvern-5-RP-1` | #10470 |
| `AlmajaraAgalacticadventureCore` | `Almajara-Core` | #10697 |

A page being edited also produced "Click and drag to move Edit Mod Name:" in an
identifier (#11446). Derive the core name from mod evidence, not page UI text.

### Revival and internal metadata

- **Revival:** reuse the frozen mod's identity and modernize the entry
  (#10280, #10588, #10637). Do not unfreeze unrelated dependencies (DEPS-04).
- **Internal `.ckan`:** remove template `depends` / `recommends` / `$vref` when
  the internal file should supply them (#10344 twice, #11165). An explicit install
  may be needed to select the correct module's internal file.
- **Superseded targets:** update relationships such as `RP-0` to `RP-1`
  (#10139, four occurrences).

### Selection and template mistakes

- Empty `find` requires a decision: #10326, #10368, #11024, #10361/#10383
  (five resubmissions), and #10213.
- A hand-built download or invented `x_netkan.github` block pins a release;
  #10623 was replaced by a `$kref` YAML submission, #10627.
- A copied template can retain the author's other mod's fields (#11179).
- A bare `VERSION` string and mismatched `NAME` silently broke AVC handling
  (#10984). Check the version-file structure.
- In #10368, `$vref` was removed because all version files belonged to bundled mods.

### Relationship, license, and tag details

- `All Rights Reserved` maps to `restricted`, even without mixed licensing
  (#10669, #10787).
- Tags were entirely absent in #10410, ba9381b6, and #10623.
- Minimum versions included `KSPCommunityFixes` 1.36.0 (#10279) and
  `KSPTextureLoader` 0.0.19 (#10870).
- Conflicts targets can be misspelled: `SpaceYCorp` to `SpaceY-Corp` (#10845).
- Only one host detected a license in d84ac784; the other needed an explicit
  field. Compare documents under VER-01.
- Duplicate relationship entries reached master: Kopernicus twice in #10697.
- Over-broad conflict-version constraints were relaxed in #10269.
- Library/Redist modules should not inherit consumer-facing recommendations
  (#11064).

## Tooling limits in the sampled environment

The forum required Chrome because plain fetches returned 403. Discord was not reachable,
and no live CKAN client resolver was available; CI sandbox install logs supplied that
evidence. SpaceDock search was name-only (`/api/search/mod?query=`). File-name
inspection was not malware scanning.

State current tool availability. Mark checks needing unavailable evidence `not
verified`; do not assume a tool exists because the historical review used it.

## Bot patterns illustrated by the sample

- Dependency detection covered a limited set of frameworks; requirements still
  needed independent review.
- Wrong/versioned `find` selections and redundant defaults were common.
- Title-derived identifiers and structural tags needed curation.
- A later bot resubmission could undo a wrangler correction (#10807).
- Tags, relationships, and install initially appeared only in the SpaceDock
  document. Check per-host fields before merging; shared fields need not all be
  duplicated.

See [Bot generation](bot-generation.md) for the heuristics. Historical success in CI is
not a guarantee that future bot submissions pass CI.

## Closure reasons recorded in the 24 unmerged PRs

These are recorded counts; do not assume the categories are mutually exclusive.

| Reason | Count |
| --- | --- |
| Duplicate entry or PR | 10 |
| Unindexable or paid dependency | 3 |
| Author withdrew or resubmitted consolidated work | 3 |
| Unresolved identifier/brand collision | 2 |
| Listing removed | 2 |
| Malware or bad faith | 2 |
| Too many concurrent PRs | 1 |
| Spec limitation | 1 |
| Author confirmed the mod was broken | 1 |
