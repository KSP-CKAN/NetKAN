# What wranglers actually fix: evidence from 2024-2026 PRs

## Contents
- The headline (fix categories by frequency, CI-caught or not)
- Rules by area: Dependencies; Relationships other than depends; Install stanza and ZIP contents;
  Identifier; Duplicates and frozen entries; Hosting and version strings; Compatibility; License;
  Tags; Name, abstract, author, resources; File format; Policy
- Patterns a completeness pass added
- Bot PR quirks worth remembering
- Closure reasons in the unmerged sample

Source: a spread sample of 112 pull requests (32 SpaceDock-bot "Add" PRs, 32 human "Add" PRs,
12 PRs labelled Fix install/license/relationships, 12 other merged PRs, 24 closed-unmerged PRs)
plus all 34 direct-to-master commits that fixed a netkan within 60 days of it being added
("review misses"). Each PR's first-submitted file was diffed against its merged state and every
reviewer comment read; the resulting rules were adversarially re-verified against the dossiers.
Frequencies are distinct PRs/commits in the sample, so treat them as relative weights.

## The headline

The CI "Inflate" check almost never fails on a submission that later needs correction. In the
bot-PR sample, NOT ONE correction was something CI flagged; every fix was a judgement call that
required the ZIP, the SpaceDock/GitHub page, the forum thread, or a grep of `NetKAN/`. Fix
categories by frequency across all 331 recorded fixes:

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

## Rules, by area (most frequent first within each area)

Severity is how wranglers treated it: **blocker** (not merged until fixed / closed),
**should-fix** (fixed before merge in nearly every case), **nice-to-have** (fixed when noticed,
often after merge).

### Dependencies

**DEPS-01 Missing transitive / companion / library dependency** (32 sources, should-fix, CI: no)
The bot only detects ModuleManager and a handful of framework nodes; it never finds the parent
mod being extended, shared libraries (`Harmony2`, `ToolbarController`, `ClickThroughBlocker`,
`SpaceTuxLibrary`, `HUDReplacer`, `TextureReplacer`, `FireflyAPI`, `KSPCommunityFixes`),
resource packs (`CommunityResourcePack`), or Kopernicus expansion components
(`VertexHeightOblateAdvanced`, `VertexColorMapEmissive`, `VertexMitchellNetravaliHeightMap`,
`ScaledDecorator`, `Singularity`, `KopernicusExpansionContinueder`, `ModularFlightIntegrator`).
How to check: grep the ZIP's `.cfg` files for `:NEEDS[...]`, `:FOR[...]`, `:AFTER[...]`, MODULE
names (`ModuleB9PartSwitch`, `ModuleWaterfallFX`, `ModuleRestockDepthMask`, `Scatterer_*`, `EVE_*`,
`TUFX_PROFILE`, `KERBALCHANGELOG`), `RESOURCE` names not in stock; read the SpaceDock description
("DEPENDENCIES:", "Requires"), the GitHub README, the forum thread, and the DLL references
(`0Harmony`, `ToolbarControl`, `ClickThroughBlocker`); compare with sibling mods by the same author.
When ilspy MCP tools are available, don't stop at string-searching the DLL — run
`get_assembly_attributes` and `list_assembly_references` on each plugin DLL and look for
`KSPAssemblyDependency` attributes and references to another mod's assembly. Treat a hit on the
identifier's own main DLL (the one matching the identifier/GameData folder) as strong `depends`
evidence; a hit only on a small integration/bridge DLL (one whose job is talking to an optional
companion mod) does not make that companion a hard dependency of the whole package — that's
`suggests` territory, not `depends`.
Reviewer quotes: "Don't forget to check the SpaceDock page, this one also had a new dependency
added after the PR was submitted." / "There's also a missing dependency here. Check the forum
thread or SpaceDock." / "Is the dependency on SSPX purely for HabUtil.dll?"
Evidence: #9937 (Singularity + KopernicusExpansion), #9980, #10191 (StationPartsExpansionRedux for
a shared DLL), #10326 (BeyondJool + VertexHeightOblateAdvanced), #10368 (Harmony2,
CommunityCategoryKit, VABOrganizer), #10505 (B9PartSwitch, ChemicalCore, CRP), #10697 (eight
Kopernicus-expansion deps added at once), #10943, #11024, #10870, #10448.

**DEPS-02 ModuleManager missing although cfgs use MM syntax** (6, should-fix, CI: warning)
CI warns "ModuleManager syntax used without ModuleManager dependency". Always act on it. Placed
first in `depends` by convention. Evidence: #10191, #10734, #10787, #11179, 79cbb53c.

**DEPS-03 Prefer the real dependency over a bundled copy** (2, should-fix, CI: no)
When the author bundles a dependency's DLL/folder, keep `depends` and `filter` the bundled copy
out instead of dropping the dependency. Quote (HebaruSan): "real dependencies should still be
preferred over bundling when possible. Let's filter out the bundled mod instead." Evidence:
#10718 (`filter: ScaledDecorator`). Exception seen: a reviewer may suggest bundling a small shared
DLL when the dependency mod is huge (#10191), so raise it as a judgement call.

**REL-03 Hard `depends` that the resolver cannot satisfy should be `recommends`/`suggests`** (2, should-fix)
Circular recommends/depends chains fail the sandbox install; optional integrations belong in
`suggests` (Debian sense: "consider also installing"), reserving `recommends` for one the resolver
should install by default. Evidence: #9896, #10226.

**PROC-02 Dependency that cannot be indexed** (3, blocker)
A required mod that is paid/Patreon-gated, or deliberately not indexed, makes the PR
unmergeable: close or label `Blocked-on-dependency`. Quotes: "This depends on a paid mod not in
CKAN." Evidence: #10448, #10736, #10826.

**DEPS-04 Dependency identifier is `.frozen`** (not a blocker, no fix needed) Distinct from
PROC-02: a frozen mod CAN be indexed and already was — freezing only stops the bot re-inflating
*future* releases, so CKAN-meta keeps serving whatever version was last indexed and a new
dependent still resolves against it. Do not propose unfreezing it (`git mv Foo.frozen Foo.netkan`)
as a correction; note it under judgement calls at most, for visibility. It IS a cue to spend an
extra minute confirming the freeze was really for inactivity and not because the host listing/repo
is gone or the author announced abandonment (that would make it a real PROC-02/DUP-02 problem, not
a frozen-mod non-issue). User correction (PR #11416, `VertexMitchellNetravaliHeightMap` frozen by
the bulk "Freeze idle mods" sweep but still live upstream): "Frozen dependencies are not a
blocker. We don't need to unfreeze them... Frozen mods are a sign that this warrants more
attention, but depending on a frozen mod is not actually an issue."

### Relationships other than depends

**REL-01 Missing `recommends`/`suggests` for companion mods** (16, nice-to-have, CI: no)
Planet packs -> `Scatterer`, `EnvironmentalVisualEnhancements`, `Firefly`, `KopernicusExpansion`,
`Singularity`, `CustomAsteroids`; parts packs -> `PatchManager`, `CryoTanks`, CRP, B9PS-based
switchers; tools -> `KerbalChangelog`. Source: SpaceDock description, README, forum thread, what
similar mods declare. Default to `suggests` for these (Debian sense: optional, worth considering);
use `recommends` only when the mod is not normally installed without the companion (e.g. it looks
broken or incomplete without it). Evidence: #10113, #10191, #10280, #10604, #10967, #10669,
#10787.

**REL-02 `supports` used backwards** (2, should-fix, CI: no)
`supports: X` means "offer THIS mod when X is installed" (the reverse of `suggests`). Authors use
it as "works with X"; rewrite as `suggests`. Evidence: #10837 (`supports -> suggests`).

**CPR-01 Missing `conflicts` for a real incompatibility** (3, should-fix, CI: no)
Same-folder installs, mods that fix the bug this mod exploits (PersistentRotationUpgraded vs
KSPCommunityFixes), fork vs original. Sources: upstream issues, forum thread, cross-check section
"other netkans referencing" and similar identifiers. Evidence: #10409, 74cb4266, #10787, #11489.

**CPR-03 Missing `provides` for interchangeable content** (3, should-fix, CI: no)
Sunflare/config packs (`Scatterer-sunflare`, `Scatterer-config`), planet-texture packs
(`ParallaxContinued-Planet-Textures`), renamed mods keep the old identifier in `provides`. Usually
paired with `conflicts` on the same virtual name. Evidence: #10026, #10787, #10477.

**META-04 Relationship target typos / wrong case** (6, should-fix, CI: no)
`VABorganizer` vs `VABOrganizer`, `EnvironmentalVisualEnhhancements`. A wrong name passes CI and
silently never resolves. Check every relationship name against `NetKAN/` exact-case (the diag
script does this). Evidence: 5efc6c04, da552012, #10734.

### Install stanza and ZIP contents

**INSTALL-02 `find` targets the wrong folder or a version-baked name** (13, should-fix, CI: only
when nothing matches). Bot picks an icons-only subfolder, a bundled base mod's folder, the wrapper
folder, or `AutophageMod0.1`. Compare `find` with the ZIP's real payload folder and with the CI
`Showing N installed files` list. Evidence: #9980, #10231, #10326, #10368, #10410, #11166, #10092,
#10498, cee18084, cb241687, d83b05c4.

Don't confuse an *unstable* wrapper folder with a *stable, shared* author/publisher namespace
folder — they take opposite fixes. An unstable wrapper (version-baked like `AutophageMod0.1`, or
an extraction artifact like GitHub's `use_source_archive` `<repo>-<sha>/`) is dropped entirely:
`find` the stable inner folder, `install_to: GameData`. A stable namespace folder the author
reuses across their own mods (`GameData/AnaAerospace`, `GameData/SterlingSystems`) is the opposite:
keep it, but move it into `install_to` and `find` only the mod-specific inner folder, so this
package's install manifest owns just its own subfolder rather than the whole shared directory —
`find: AnaAerospace, install_to: GameData` makes `GameData/AnaAerospace` itself one of this
module's installed paths, which a second mod by the same author reusing that same stanza would
also claim, conflicting; `find: RebalancedFuelCost, install_to: GameData/AnaAerospace` installs to
the identical on-disk path but only claims the `RebalancedFuelCost` subfolder. Precedent: the
`SterlingSystems*` netkans all do `find: <Module>, install_to: GameData/SterlingSystems` (e.g.
`SterlingSystemsEngines.netkan`: `find: Engines`). Evidence: #11493 (SimpleRebalancedFuelCosts).

**INSTALL-01 Redundant explicit install stanza** (9, nice-to-have but done almost every time)
When identifier == GameData folder, delete the `install` block ("Use default install stanza",
"Identifier matches folder name"). Evidence: #9937, #10150, #10697, #10776, #11166, #10942, #11143,
6aef8288.

**INSTALL-03 Optional content needs `filter` or its own module** (3, should-fix, CI: no)
`Patches`/`Extras` folders, files shared with a sibling mod (real file-conflict bug in #10179),
per-file craft stanzas collapsed to one folder stanza (#10008), runtime-rewritten files filtered
so `install_size` stays sane (#10588 `filter: HETTN.TechTree`). Evidence: #10034, #10179, #10008.

**SPLIT-01 Two mods (or mutually exclusive variants) in one ZIP need separate netkans** (7,
should-fix, CI: no). 2D/3D variants, core + optional pack, agency/flags shared between siblings,
RP-1 config vs parts. Wire them with `depends`/`suggests`/`conflicts` and `filter` on the parent.
Evidence: #9980, #10470, #11024, #10034, #10179, #10669.

**SPLIT-02 MM patches must use `:NEEDS[Other]`, never `:FOR[Other]`** (1, blocker)
`:FOR[X]` where X is not this mod makes ModuleManager believe X is installed. Quote (JonnyOThan):
"you must not use `FOR` with an identifier that isn't your mod." Evidence: #10470.

**INSTALL-04 Platform-dependent `GameRoot` targets are impossible** (1) `KSP_Data` vs
`KSP_x64_Data` cannot be expressed; label `Blocked-on-CKAN-feature`/ask the author to repackage.
Evidence: #10116 (abandoned after 8 months).

**PROC-03 Malware / bad-faith** (2, blocker) A netkan with `find: GameData, install_to: GameData`
from a throwaway account and a vague abstract was closed as "Malware." (#10285); a hostile
trademark-dispute submission was closed (#10046). Signals: whole-GameData catch-all installs,
no real description, retaliatory wording.

### Identifier

**IDENT-01 Identifier must match the GameData folder or plugin DLL** (11, should-fix; CI only
errors when identifier != filename). Rename identifier AND file; then INSTALL-01 usually applies.
Quotes: "CKAN can only auto-detect installs if the DLL name matches the mod's identifier." /
"the ckan spec recommends using the same name in the mod's install directory as the mod's
identifier." Evidence: #9937 (`JFAJebFarAway -> JebFarAway`), #10150 (`AtmosphericMinmus ->
MinmusAtmosphere`), #10231 (renamed DLL), #10280 (branding suffix dropped), #10368 (60-char bot
identifier trimmed), #10697 (`Almajara-Core`, `Almajara-LastLights` to match folders), #11097,
#11143, #10669, #10080.

**IDENT-02 Identifier collides with an existing mod's name/brand** (3, blocker)
`Kerbcam` vs existing `KerbCam`, `XenonISRU` already used; `Archipelago` renamed `KSPArchipelago`
to avoid the wider project's name. Case-insensitive grep of `NetKAN/` and a status-page lookup.
Evidence: #9908, #11291, #11143.

Bot quirk: a SpaceDock page mid-edit yields garbage identifiers (UI placeholder text scraped into
the name); catch on sight.

### Duplicates and frozen entries

**DUP-01 Mod already indexed or already has an open PR** (12, blocker)
Check `NetKAN/*.netkan` and `*.frozen` for the same SpaceDock id / GitHub repo / folder name,
the open PR list, and recently closed PRs. Reviving a frozen identifier: reuse it and delete the
`.frozen` (#11097 DiscordRP, #10280 Droptank Wrapper unfrozen). Quotes: "Duplicate of #10460",
"There's already a mod called KerbCam (see #4031)", "can you please stop opening and closing PRs
to add a mod that's already indexed?" Evidence: #10663, #10428, #11163, #11291, #11446, #10984.

**DUP-02 Mod removed from its host** (2) SpaceDock listing deleted before merge -> close (#10338,
#10949); existing netkans get frozen when the host listing is gone and the author announced
abandonment (#9900, #10257).

**PROC-01 One PR per netkan at a time** (2, nice-to-have) "may I strongly recommend one pull
request per netkan at one time?" (#10892); repeated open/close churn (#10984).

### Hosting and version strings

**KREF-02 Missing second host (multi-hosting)** (4, should-fix, CI: no)
When SpaceDock and GitHub both carry releases, index both (fallback downloads). Verify a
SpaceDock id attached to a sub-module really is that sub-module and not the parent/sibling.
Evidence: #10637, #11016, 810660c1.

**KREF-01 `$kref` target renamed/removed** (6, blocker when it 404s; CI errors on download
failure). Repos get renamed mid-review (#10184), SpaceDock listings get renamed (#10213) or
deleted (#10338, #10949). Open the SpaceDock/GitHub URL from facts.

**VER-04 GitHub release without assets** (1, should-fix, CI: FATAL crash) "it failed because the
ZIP file wasn't attached to the release on GitHub, so I have told it to only check SpaceDock."
Either drop the GitHub document, set `use_source_archive` if the repo IS the mod, or ask the
author to attach the ZIP. Evidence: #10604.

**VER-05 Multi-asset GitHub release needs `asset_match`** (2, should-fix, CI: no unless it
picks the wrong one and fails). Negative look-ahead to exclude a flag pack:
`/asset_match/^(?!.*Flagpack)`; `version_from_asset` to split one release into modules.
Evidence: #10942, #10477.

**VER-01 Version flags not mirrored across host documents** (7, should-fix, CI: no)
`$vref`, `x_netkan_version_edit`, `x_netkan_force_v`, `license` set in one document but not the
other; the hosts then produce different version strings for the same release and CKAN shows two
entries. Compare documents side by side and compare the two inflated `version` values. Quotes:
"Both hosts have v prefix", "need this on both?". Evidence: #10565, #10807 (re-broken by a bot
resubmission), #11070, e6249486, 88183e87, e2e916e4, 0dea2625. This is the single most common
review MISS in the post-merge sample.

**VER-02 `x_netkan_version_edit` regex too strict for later releases** (4, should-fix, CI: no
at review time; the bot errors later). A mandatory space or dot in the regex breaks on the next
tag. Prefer `^v?(?<version>.+)$` or `^[vV]?\.?(?<version>.+)$`; apply the regex to ALL recent tags
(facts: `version_edit_applied`). Evidence: a41a13e7, d78cd3b2, a580eda4, 2560756a.

**VER-03 Release tag is not a version** (1, should-fix) Tag `stable_release` would become the CKAN
version; ask the author to retag (`v1.0`). Evidence: #10877. Also: once a mod has been indexed
with a `v` prefix, later hosts must match (`x_netkan_force_v: true`, 1f32646d CareerReimagined).

### Compatibility

**GVER-01 Hard-coded `ksp_version*` instead of `$vref`** (5, nice-to-have -> should-fix when a
`.version` exists). Remove `ksp_version_min/max` and add `$vref` when the ZIP has a `.version`
file (#10323, #11235, #11016 added `$vref`); collapse min/max to the `ksp_version` shorthand when a
pin is genuinely needed (#11143). Pins are acceptable when there is no `.version` file and the host
gives nothing (#10747 set min 1.8 / max 1.12).

**VREF (post-merge misses)** `$vref` missing on the GitHub document while present on the SpaceDock
one, or missing altogether though the ZIP ships a `.version` file: 88183e87, e2e916e4, 0dea2625,
#11250. CI warns "$vref is not ksp-avc, version file present" - act on it.

### License

**LIC-01 License missing, invalid, stale, or unverified** (13, should-fix; CI fails only on an
invalid string). SpaceDock free text ("MIT (configs)/ARR (assets)", "CC BY-NC-ND 4.0") -> invalid
-> set a valid value; "All Rights Reserved" -> `restricted`; GitHub auto-detect fails when there is
no machine-readable LICENSE -> set explicitly; a hand-typed value that duplicates what the host
supplies should be removed (7eb28657 "Get KerbalCalculator license from GitHub"); on multi-host
files the license may be needed in the GitHub document specifically (d84ac784). Evidence: #10842,
#10669, cdc46971, 76b59b9a, #11508.

**LIC-02 Mixed licensing -> single most restrictive value** (3, should-fix) "Most restrictive
license takes precedence" (#10787 collapsed `[restricted, CC-BY-NC-ND]` to `restricted`); art ARR +
code CC0 -> `restricted` (#10842).

### Tags

**TAGS-01 Bot/author tags do not match the Suggested Tags guide** (16, should-fix, CI: no)
Drop `config` when `planet-pack`/`parts` already describe the content; drop `plugin`/`crewed`/
`first-person` that came from a bundled dependency or a stray cfg; add `physics`, `science`,
`graphics`, `app`, `library`, `flags`, `resources`, `crewed` from the description; reject invented
tags (`gameplay`, bc31f731). Evidence: #9895 (+flags), #10113 (-config), #10368, #10776 (+physics),
#10877 (config+plugin -> plugin+crewed), #11097 (+app), #11166 (-config +science), #10669.

### Name, abstract, author, resources

**META-01 Do not hard-code what the host fills in** (16, nice-to-have but routinely stripped)
`name` (when equal to the host's), `author`, `license`, `spec_version`, `resources.homepage/
repository/bugtracker`, `release_status`, `ksp_version_min`. Quote: "you can set the homepage link
by setting the Website link for the repo on GitHub; the CKAN bot will pull it into the metadata
automatically." Evidence: #10150, #10191, #10323, #10477, #10669, #10747.

**META-02 Author credit incomplete / bot credited** (4, nice-to-have) Add original authors of
continued/redux mods (991f0e4d Coatl, #10604 FuelWings), missing co-authors (8039f96e), and set
`author` explicitly when the host would attribute a bot account (#9929 "Set author to avoid
adding a bot").

**META-03 / META-04 Name typos and branding** (6+3, should-fix) Hyphenation, missing words
("Institute"), copy-paste variant numbers (8k vs 16k), trailing whitespace, self-referential
abstracts. Evidence: #10184, 30de8b64, c3492a6b, 3da43ce7, #10734.

**YAML-04 Abstract unreadable** (3, nice-to-have) "After reading this abstract, I did not
understand what the mod does." Rewrite from README; use `>-` folded scalars for long text; keep
`description` for detail. Evidence: #10026, #10734, #11143.

**HOMEPAGE** (10 fixes) Forum thread preferred over GitHub URL; empty SpaceDock website -> set
`resources.homepage` explicitly; GitHub-only mods should set the repo Website field instead.

### File format

**YAML-01 Syntax errors that CI may NOT catch** (3, blocker) A missing colon after `depends`/
`supports` can parse as a scalar and silently drop the whole block (effc85a1 shipped to master
with CI green). Inspect the inflated `.ckan` for missing blocks, not just the parse result.
Evidence: #10734, effc85a1.

**YAML-03 Convert JSON to YAML when touching a file** (4 confirmed, nice-to-have) New files
should be YAML; hand-written JSON with errors was abandoned and resubmitted as `$kref` YAML
(#10623 -> #10627). Evidence: #11016, #11143, #11235.

**XNK-01 `x_via` marker** (9, nice-to-have) Often deleted when a wrangler rewrites the file, but
13+ merged PRs kept it; do not report it as a correction on its own.

### Policy

**POLICY-01 Permission for re-uploads, forks, derivatives** (3, blocker)
Quotes: "could you please provide some proof that you have permission from the author to
distribute these? We take mod authors' rights seriously" / "CKAN as a matter of policy only adds
mods if the authors agree. Have these authors agreed? If so, please add a link to where they
agreed in the body/description of this pull request for posterity." Evidence: #9895 (held for a
Reddit comment), #10715 (held ~1 month), #10046.

## Patterns a completeness pass added (each seen 2-6 times in the raw findings)

- **IDENT-03 Bot identifier is the whole marketing title.** `KerbalHacksDroptankWrapperRecolorProjectFelota`
  -> `KerbalHacksDroptankWrapperRecolor` (#10280); `UnmanagedAngerResourcesforKerbalismVABoPrunesCCKConfigToolsPrunes`
  -> `UnmanagedAngerResources` (#10368); `ArcAerospaceWyvernCapsuleRP1Config` -> `Wyvern-5-RP-1`
  (#10470); `AlmajaraAgalacticadventureCore` -> `Almajara-Core` (#10697); a SpaceDock page mid-edit
  produced "...Click and drag to move Edit Mod Name:" inside the identifier (#11446).
- **Reviving a `.frozen` entry.** When a new submission IS the frozen mod itself coming back under
  its own PR, reuse the frozen identifier, delete the `.frozen`, and modernise (JSON->YAML,
  install, `$vref`, version-string cleanup, MM dep, name): #10280, #10588, #10637. This does NOT
  extend to a different, new mod merely depending on a frozen one — see DEPS-04: that's not an
  issue and needs no unfreezing.
- **Internal `.ckan` overrides.** Once a mod ships its own `.ckan`, the netkan's static
  `depends`/`recommends`/`$vref` should be removed so they do not fight the internal file
  (#10344 x2, #11165), and the netkan may need an explicit `install` stanza so the override
  attaches to the right module.
- **Stale outbound relationship targets.** `recommends`/`suggests` pointing at a superseded
  identifier (`RP-0` -> `RP-1`, #10139 x4). Point at the current identifier.
- **"All Rights Reserved" alone -> `restricted`** (#10669, #10787), independent of mixed licensing.
- **`find: ''`** literal from the bot: #10326, #10368, #11024, #10361/#10383 (fixed only after five
  resubmissions), #10213. Always a decision for a human.
- **Hand-built `download:` URL / custom `x_netkan.github` block instead of `$kref`** (#10623):
  pins one release forever; the PR was abandoned and resubmitted as a `$kref` YAML (#10627).
- **Template leftovers** (#11179): a file whose identifier/`$kref`/tags/depends came from the
  author's OTHER mod. Check that the content matches the `$kref` target.
- **AVC `.version` shape** (#10984): `VERSION` as a bare string instead of `{MAJOR,MINOR,PATCH}`
  plus a `NAME` mismatch broke `$vref` silently.
- **`$vref` against someone else's `.version`** (#10368): the only `.version` files belonged to
  bundled third-party mods; `$vref` was removed.
- **Tags entirely absent** (#10410, ba9381b6, #10623), not just wrong.
- **Version-constrained dependencies**: `KSPCommunityFixes min_version: 1.36.0` (#10279),
  `KSPTextureLoader min_version: 0.0.19` (#10870).
- **Typos in `conflicts` lists too**: `SpaceYCorp` -> `SpaceY-Corp` (#10845).
- **License parity across host documents** (d84ac784): only one host auto-detects, so the other
  document needed `license` explicitly. Same "mirror across documents" logic as VER-01.
- **Duplicate relationship entries** shipped to master (`Kopernicus` twice, #10697).
- **Over-broad `conflicts` version constraints** get relaxed once the old version is gone (#10269).
- **Library/"Redist" modules must not inherit consumer-facing `recommends`** (#11064).

Tooling limits for an automated reviewer: the forum is readable only through the Chrome tools
(plain fetches get 403), Discord is not reachable, there is no live CKAN client resolver (use
the CI sandbox install log instead), SpaceDock search is by name only (`/api/search/mod?query=`),
and there is no malware scanning (only file-name inspection). Say "not verified" for anything
that needs those.

## Bot PR quirks worth remembering
- Bot netkans never fail CI; every fix is judgement.
- `depends` detection stops at ModuleManager plus one obvious framework.
- `find` mis-resolution (wrong folder, version-baked folder, `find: ''`) is the most common
  install problem; the second is a redundant default stanza.
- Identifier = SpaceDock title with punctuation removed; always re-derive from the folder/DLL.
- Tags are structural (`config` for any cfg, `plugin` for any DLL); descriptors must be added.
- A later bot resubmission can silently undo a wrangler's fix (#10807).
- The GitHub document gets no tags/depends/install; make both documents consistent.

## Closure reasons in the unmerged sample (24 PRs)
Duplicate of an existing entry or PR (10), unindexable/paid dependency (3), author withdrew or
resubmitted consolidated work (3), identifier/brand collision left unresolved (2), listing taken
down (2), malware/bad faith (2), too many concurrent PRs (1), spec limitation (1), mod confirmed
broken by its author (1).
