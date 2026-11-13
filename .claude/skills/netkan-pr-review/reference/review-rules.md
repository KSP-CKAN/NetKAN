# NetKAN review rules

Apply every section when reviewing a submission. The workflow, severity
definitions, verdict order, and report template are in [SKILL.md](../SKILL.md).

Each named heading identifies one rule. Keep its requirement, exceptions, and
evidence together when editing. The 3a-3k section numbers retain the checklist's
existing references.

## 3a. Gatekeeping

Failure of any rule in this section makes the verdict `BLOCKED`.

### GATE-PERMISSION: Confirm author permission

- For a bot PR, the SpaceDock uploader (`author` or `shared_authors`) must be the
  mod's author or maintainer. Compare those names with the GitHub owner.
- For a third-party human PR, find the author's approval in the PR body or a
  forum/GitHub post. If you find approval yourself, permission passes; ask for
  its link to be added as a judgement call, rather than a BLOCKER.
- If approval cannot be found, block the submission.
- An author's statement such as "not on CKAN until it is stable" is a refusal
  until the author revokes it. Never index authors on the opt-out list.

### GATE-GAME: Confirm KSP1

Check SpaceDock `game_id: 3102`, `.version` `KSP_VERSION` 1.x, and absence of
`swinfo.json`.

### GATE-DUPLICATE: Check for an existing submission or indexed mod

Check for the same SpaceDock ID, GitHub repository, folder, or DLL. Also check:

- A `.frozen` twin: reuse it.
- Case-insensitive or similar identifiers.
- SpaceDock search hits under another ID and status-page entries.
- Another open PR for the mod (`OTHER OPEN PRs` in facts). Keep one PR per
  netkan, normally the earlier submission or the author's own.

Forks of indexed mods need decisions about `conflicts`, `provides`, and `replaced_by`.

### GATE-HOST: Confirm an indexable download

Require an indexable host with a real ZIP asset. See
[Spec cheatsheet](spec-cheatsheet.md) for supported `$kref` hosts and options.

## 3b. Identifier

### ID-FORMAT: Match the filename and identifier syntax

The identifier must match `^[A-Za-z0-9][A-Za-z0-9-]+$` and equal the filename
stem in every document.

### ID-NAME: Use the mod's core name

Remove versions, game versions, "WIP", author or host names, and subtitles.
Bot identifiers are SpaceDock titles with punctuation removed; prune them when
the title contains a colon, pipe, or parenthetical. Follow sibling conventions
in `NetKAN/`, such as `Foo-Textures` and `TURD-Bar`.

### ID-INSTALL: Prefer the folder or DLL name

The identifier should match the GameData folder, or a plugin's DLL base name.
This enables the default install and detection of manual installs. A mismatch
without a stated reason is SHOULD-FIX. If the author explains the mismatch,
consider that explanation before proposing a rename.

## 3c. Hosting and YAML documents

### HOST-FALLBACK: Include usable download hosts

When both SpaceDock and GitHub have releases, include both documents for fallback
downloads. Drop a GitHub document whose releases have no asset.

GitHub's automatic source ZIP (`use_source_archive`) wraps the repository in
`<repo>-<sha>/`; it is not a packaged mod by default. Accept it only if the ZIP
contains the mod folder and the install stanza uses `find` on that folder.

### HOST-FIELDS: Repeat fields that are processed before merging

NetKAN applies per-document fields before merging the results. Repeat these in
every document where they are needed:

- `$vref`.
- `x_netkan_version_edit`.
- `x_netkan_epoch` / `force_v`.
- `license` when the host cannot supply it.
- `install` when the two ZIP layouts differ.

Missing `$vref` in one document is SHOULD-FIX under the "vref in both sections"
house convention; it is not itself a CI error. Tags, relationships, and name can
live in one document, conventionally the SpaceDock document.

### HOST-GITHUB: Check repository and release selection

Check `archived`, `fork` (is this the canonical repository?), `prereleases`, and
`asset_match` when a release contains several ZIPs. In facts,
`version_edit_applied` shows each tag's resulting version; `null` means
`strict: true` fails on that tag.

## 3d. Version string

### VERSION-MATCH: Generate the same version on every host

Every host must yield the identical string for a release. For example,
"Generated 2 modules but only 1 requested: X on github.com; vX on spacedock.info"
is a failure.

Fix such a mismatch with the same
`x_netkan_version_edit: ^v?(?<version>.+)$` (or `[vV]`) in every document,
including SpaceDock. A `v` or `V` prefix shared by all hosts is fine; do not
request an edit merely to strip it.

### VERSION-SOURCE: Let `$kref` supply version and download

Do not hard-code `version` or `download` alongside `$kref`. For epochs and
out-of-order versions, see [Uncommon cases](uncommon-cases.md).

## 3e. Compatibility

### COMPAT-VREF: Use an installed version file

If the ZIP ships an installed `.version` file, require
`$vref: '#/ckan/ksp-avc'` in every document. Use the path form when there are
several `.version` files.

The file must belong to this mod and contain valid JSON with
`{MAJOR, MINOR, PATCH}` objects. Check the `.version note` lines in facts.

### COMPAT-HOST: Avoid redundant compatibility fields

Do not hard-code `ksp_version*` when `$vref` or SpaceDock supplies compatibility.

## 3f. Install stanza

Use the latest ZIP facts. Compare the ZIP listing, approximate install, and
`Showing N installed files` output.

### INSTALL-CONTENT: Install the mod's intended content

Install the mod's own folders. Put craft files the player is meant to fly under
`Ships/...`.

Exception: a contract or mission-prop craft referenced by `craftURL` or a similar
GameData-relative path in a `.cfg` must stay in GameData, or the reference breaks.
See [Spec cheatsheet: install](spec-cheatsheet.md).

### INSTALL-DEFAULT: Remove a redundant default install

If the identifier equals the sole GameData folder, omit the `install` block.

### INSTALL-FIND: Select a stable mod folder

- `find: ''` is a BLOCKER: select the folder explicitly.
- Replace `find: GameData`, release-specific `file:` paths, and version-numbered
  or space-containing wrapper folders with `find` on the stable inner mod folder
  and `install_to: GameData`.

### INSTALL-NAMESPACE: Preserve stable author namespaces without owning siblings

A stable namespace shared by an author's own mods, such as
`GameData/AnaAerospace` or `GameData/SterlingSystems`, is not an unstable wrapper.
Preserve it in the installed path.

Do not use `find: <namespace>, install_to: GameData`: that makes this module own
the entire namespace and conflict with sibling mods. Instead, find only the
mod-specific inner folder and put the namespace in `install_to`.

For example, the `SterlingSystems*` netkans use:

```yaml
find: Engines
install_to: GameData/SterlingSystems
```

This preserves the on-disk layout while limiting ownership to this mod's subfolder.

### INSTALL-OTHER-MOD: Check installs inside another mod's folder

If `find`, `file`, or `install_to` names another indexed mod's folder (such as
`TUFX` or `Kopernicus`), check the actual paths:

- **A path collides with a file the target mod ships:** BLOCKER. CKAN cannot
  overwrite another mod's files.
- **A uniquely named add-on file does not collide:** default to SHOULD-FIX and
  recommend this mod's own folder. Frameworks such as TUFX and ModuleManager
  generally scan all of GameData for profiles or patches.
- **Matching sibling precedent exists:** the non-colliding install can pass, but
  confirm that the siblings also install into that folder. Merely depending on
  the same target is not precedent; one outlier among many contrary siblings is
  not enough.

To check precedent, search `NetKAN/` for `name: <Target>`, then read each match's
`install` stanza. See [Spec cheatsheet: install](spec-cheatsheet.md) for ownership rules.

### INSTALL-FILTERS: Exclude unrelated files

Exclude source code, `.pdb`, `__MACOSX`, `Thumbs.db`, `.git*`, optional `Extras`,
and player-launchable craft files from GameData using `filter` or
`filter_regexp`. Keep contract-prop craft there (INSTALL-CONTENT).

Junk contained inside the mod's own folder is acceptable.

## 3g. Bundled third-party mods

### BUNDLE-SEPARATE: Exclude bundled mods and declare relationships

Exclude another mod's folders or DLLs from this mod's install, and declare the
appropriate relationship: `depends` if required, or `suggests` / `recommends` if
optional under section 3h. Installing a bundled copy conflicts with the real mod
and is a BLOCKER.

Check `bundled_candidates` in facts. Examples include ModuleManager,
Toolbar/ToolbarControl, ClickThroughBlocker, Kopernicus, B9PartSwitch,
Firespitter, CRP, a MiniAVC folder, Waterfall, Scatterer, TUFX, and 0Harmony.

## 3h. Relationships

### REL-REQUIRED: Depend on everything needed for the mod's function

Use `depends` when the mod cannot function or has no purpose without the target,
even if its absence causes no crash. This includes content-only packs that exist
solely for another mod to consume, such as decals selected through
ConformalDecals' menu. Add `min_version` when a newer dependency release is needed.

Look for evidence in:

- ModuleManager syntax.
- CFG `:NEEDS`, `:FOR`, and MODULE names, including Kopernicus, Waterfall,
  B9PartSwitch, TUFX, ContractConfigurator, KerbalKonstructs, Scatterer/EVE,
  Harmony2, and ToolbarController/ClickThroughBlocker.
- Description or README statements of requirements, `.version`, and sibling mods.

Interpret those clues in context: optional integration is not automatically a
hard dependency. The bot usually finds only ModuleManager and one obvious
framework; missing dependencies are the most frequent wrangler correction.

If a precedent uses `recommends` for an inert content-only pack, flag the precedent
as potentially too soft rather than copying it. For example, GRIT (PR #11400)
correctly depends on ConformalDecals even though `ISO-7010-Decals.netkan`, a
similar flags pack, uses `recommends`.

### REL-DLL: Distinguish main-plugin dependencies from optional bridges

When ilspy MCP tools are available, run `get_assembly_attributes` and
`list_assembly_references` on each DLL in the ZIP rather than relying on string
searches.

A `KSPAssemblyDependency` attribute or reference to another mod's assembly is
hard-dependency evidence when found on the mod's own main DLL (matching the
identifier or GameData folder). The same reference on a small integration or
bridge DLL for an optional companion does not make that companion required for
the whole package; use `suggests` for that integration.

### REL-TARGETS: Resolve relationship names exactly

Use existing identifiers with exact case. Facts marks valid targets as `ok`,
`virtual`, or `dlc`. Treat `UNKNOWN` and `WRONG CASE` as BLOCKERs and correct the
relationship name. Use current identifiers rather than superseded ones.

A required dependency that cannot be indexed (for example, paid, Patreon-gated,
or deliberately excluded) makes the verdict `BLOCKED`.

A `frozen` target alone needs no correction: freezing stops future inflation,
while CKAN-meta continues serving the last indexed version. Note it under
judgement calls for visibility and investigate why it was frozen:

- Inactivity alone is not a problem.
- A removed host listing/repository or an author announcement of abandonment is
  a real concern (the DUP-02 case in the supporting references).

Never propose unfreezing as the correction. A target marked `only in CKAN-meta`,
with no current NetKAN entry, still needs discussion.

### REL-OPTIONAL: Choose the relationship by its effect on this mod

Use Debian-style meanings:

| Relationship | When to use it |
| --- | --- |
| `depends` | This mod cannot function or has no purpose without the target (REL-REQUIRED). |
| `recommends` | Users would not normally install this mod without the target, but this mod still does something by itself or there is a legitimate reason to skip the target. It is near-mandatory in practice and installed by default. |
| `suggests` | An optional enhancement or integration that users can take or leave. Default to this for optional companions. |
| `supports` | Offer this mod when the other is installed. Authors sometimes use it backwards when they mean `suggests`. |
| `conflicts` | Same-folder, same-DLL, or otherwise incompatible mods, including forks of indexed mods. |

"Works great with", "adds support for", and "compatible with" usually justify
`suggests`. Reserve `recommends` for cases where the mod is crippled, visually
broken, or missing core content without the companion, while still satisfying
the distinction from `depends` above.

### REL-PRECEDENT: Use house style with the functional rules above

Consult precedent netkans in facts. For example, `KerbalChangelog` is `suggests`,
profile packs depend on their framework, and "Redist" modules carry no
`recommends`.

If precedent uses `recommends` for an apparently optional integration, flag a
judgement call toward `suggests` rather than silently copying it. Apply the same
principle to content packs covered by REL-REQUIRED.

## 3i. License

### LICENSE-VALUE: Use the spec's license vocabulary

Use a valid spec string from [Spec cheatsheet](spec-cheatsheet.md). SpaceDock
free-text licenses are a common CI FATAL.

### LICENSE-EVIDENCE: Match the distributed license

Compare the ZIP's LICENSE and README, GitHub `license_spdx`, and SpaceDock field.
Use `restricted` for mixed licensing or "All rights reserved"; use `unknown`
when genuinely unknown.

### LICENSE-HOST: Override only when needed

Do not restate a license the host supplies. Set it in a document whose host
cannot supply it.

## 3j. Tags, display fields, and hygiene

### META-TAGS: Curate tags from the approved vocabulary

Use only Suggested Tags. Review the bot's structural guesses (`config` for any
CFG, `plugin` for any DLL) and add descriptors supported by the description.
Missing tags are SHOULD-FIX.

### META-HOST: Avoid redundant host fields and supply missing information

Do not hard-code `name`, `abstract`, `author`, `resources.*`, or `ksp_version`
that the host already provides.

Set `resources.homepage` to the forum thread when the host lacks it. Set `author`
when the uploader is not the author; include original authors of continued mods.

### META-GENERATED: Remove fields produced during inflation

These fields belong in generated `.ckan` files, not handwritten netkan templates:

```text
spec_version
release_status
download_size
download_hash
download_content_type
install_size
release_date
x_generated_by
x_netkan_version_pieces
```

Their presence usually indicates a copied inflated `.ckan`. Mark SHOULD-FIX and
delete the field. See [Spec cheatsheet: Bot-generated fields](spec-cheatsheet.md)
for the rationale for each field.

### META-SYNTAX: Keep metadata consistent

Prefer YAML, quote `$kref` and `$vref`, and do not mix JSON with YAML. Correct
misspelled keys such as `licence`, `dependencies`, and `version_min`. Remove
duplicate relationship entries. `x_via` may stay.

### META-INTERNAL: Do not duplicate an internal `.ckan`

If the ZIP includes an internal `.ckan`, do not restate what it supplies. See
[Uncommon cases](uncommon-cases.md).

## 3k. Could the mod function?

### SANITY-SCOPE: Perform a brief static check

Spend at most a few minutes using facts and the ZIP listing. Look for reasons
the mod cannot function; this is not a code-quality review or an in-game test.

| Check | Evidence to look for |
| --- | --- |
| Payload | No GameData content; source/docs/screenshots only; or an empty/tiny installed-files list missing the DLL, parts, or CFGs promised by the description. |
| Plugins | An actual DLL, rather than only `.cs` / `.csproj`. With ilspy, check references to KSP1 `Assembly-CSharp` / `UnityEngine`, rather than KSP2 or another engine, and a loadable target framework (net4x/netstandard2.0; `net6.0`+ will not load). Missing assembly dependencies belong under 3h. |
| Parts and content | Each CFG `PART` has its `mesh` / `MODEL` (`.mu` / `.dae`) and textures in the ZIP. CFGs are not all empty, obviously unbalanced, or unedited templates. |
| Patches | ModuleManager patches target stock content or a declared dependency. A patch for a mod that is neither installed nor a dependency does nothing. |
| KSP version | The `.version` / SpaceDock range is not obviously unusable for KSP1. An old KSP 0.x or 1.0-1.2 plugin is likely broken on current KSP; raise a judgement call. |
| Placeholder uploads | Description or files identify an empty stub, template, joke, or test upload. |
| Author statements | Description, README, or forum says the mod is broken, WIP-unplayable, or requires something unavailable, such as a paid or removed mod. |

### SANITY-OUTCOME: State the result and its limits

Choose one result:

- `plausible`: no reason found that it cannot work.
- `doubtful: <reason>`: raise a judgement call with evidence.
- `cannot work: <reason>`: BLOCKER, with verdict `BLOCKED: mod cannot function`.

Say `static check only`; never claim in-game testing. If a check requires missing
evidence, such as DLL references when ilspy is unavailable, mark it `not verified`.
