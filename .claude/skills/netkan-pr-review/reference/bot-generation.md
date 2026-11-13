# SpaceDock bot submissions

Use this reference to understand how a bot-generated netkan was produced and
which choices need review. These are generation heuristics, not acceptance rules.
Apply [Review rules](review-rules.md) to decide whether the result is correct.

Source: `KSP-CKAN/NetKAN-Infra`, `netkan/spacedock_adder.py` and
`netkan/mod_analyzer.py`. When updating this file, keep each heuristic beside its
review implication. Preserve literal field names and regexes.

## BOT-PR: How the PR is created

When an uploader selects "Add to CKAN", `netkan-bot` opens a PR with:

| Item | Generated value |
| --- | --- |
| Title | `Add <SpaceDock name> from SpaceDock` |
| Branch | `add/<identifier>` |
| Label | `Mod request` |
| Body | SpaceDock name, authors, abstract, license, size, homepage, and source link |

An uploader's request establishes consent only if the uploader is the author or
maintainer. See GATE-PERMISSION in the review rules.

## BOT-ID: How the identifier is chosen

The bot uses `re.sub(r'[\W_]+', '', spacedock_name)`: remove punctuation,
whitespace, and underscores from the display name.

| SpaceDock title | Generated identifier | Review implication |
| --- | --- | --- |
| Kerbal 3D Exporter | `Kerbal3DExporter` | May already be suitable |
| Almajara: A galactic adventure: Core | `AlmajaraAgalacticadventureCore` | Remove the subtitle |
| KH's Better Mun | `KHsBetterMun` | Check the core name and installed folder |
| Star Strider \| Stock-alike Crew Spacecraft | `StarStriderStockalikeCrewSpacecraft` | Remove the subtitle |

The filename follows the identifier. Proposing a different identifier also means
proposing a file rename.

## BOT-DOCUMENTS: Which YAML documents are generated

### GitHub document

If SpaceDock's source-code link identifies a GitHub repository with at least one
release, the bot creates a first document with
`$kref: '#/ckan/github/<user>/<repo>'`.

| Condition | Generated field | What to verify |
| --- | --- | --- |
| Latest release has no assets | `x_netkan_github: {use_source_archive: true}` | The source archive must contain an installable mod layout. Otherwise drop the GitHub document. |
| Latest tag has text before its first digit | `x_netkan_version_edit: '^<prefix>?(?<version>.+)$'` | The bot checks only the latest tag. Test recent tags too, especially mixed styles such as `v`, `V`, or `release-`. |
| Asset ZIP contains a `.version` file | `$vref: '#/ckan/ksp-avc'` | The version file must belong to this mod and be installed. |

### SpaceDock document

The second document contains `identifier`, `$kref: '#/ckan/spacedock/<id>'`, an
optional `$vref`, the analyzer's tags/relationships/install, and
`x_via: Automated SpaceDock CKAN submission`.

The bot places tags, dependencies, and install instructions only in the SpaceDock
document. Per-host inflation therefore differs before the documents are merged.
Shared tags and relationships can remain in one document; repeat fields that
are processed before merging as required by HOST-FIELDS. Keep both usable hosts
for fallback downloads, or drop a GitHub document with no usable release.

## BOT-ANALYZER: How tags and dependencies are guessed

The analyzer matches regexes against CFG content and ZIP filenames:

| Signal | Tags added | Dependency added |
| --- | --- | --- |
| MM syntax (`^[@+$-!%]` or `^NAME:`) | | ModuleManager |
| `PART {` | parts; removes config | |
| `INTERNAL {` | crewed, first-person | |
| `PROP {` | first-person | |
| `@TechTree` | tech-tree | |
| `@Kopernicus` | planet-pack | Kopernicus |
| `STATIC {` | buildings | KerbalKonstructs |
| `TUFX_PROFILE` | graphics | TUFX |
| `CONTRACT_TYPE` | career | ContractConfigurator |
| `@CUSTOMBARNKIT` | | CustomBarnKit |
| `name = ModuleB9PartSwitch` | | B9PartSwitch |
| `name = ModuleWaterfallFX` | graphics | Waterfall |
| `VertexMitchellNetravaliHeightMap` | | VertexMitchellNetravaliHeightMap |
| `*.ks` | config, control | kOS |
| `swinfo.json` | | SpaceWarp; indicates KSP2 |
| `*.dll` | plugin | |
| `*.cfg` | config | |
| `*.patch` | config | PatchManager |
| `/Spaces/` or `/Props/` | first-person | |

Review implications:

- Tags describe detected structure, not necessarily the mod's purpose. A settings
  CFG can trigger `config`; one Waterfall module can trigger `graphics`.
- Descriptors such as science, career, control, information, editor, convenience,
  resources, combat, comms, uncrewed, sound, flags, agency, suits, library, app,
  physics, and planet-pack appear only when a matching heuristic fires. Curate
  tags against the description and the Suggested Tags vocabulary.
- Dependency detection covers only the table. Check other requirements yourself,
  including Firespitter, CommunityResourcePack, B9 wings, Scatterer, EVE, Parallax,
  ReStock, and KSPCommunityFixes.
- Optional or Extras patches can trigger ModuleManager detection too. Establish
  which content is actually installed before deciding the relationship.

## BOT-INSTALL: How `find_folder` chooses an install

The folder-selection logic is:

| ZIP layout | Selected source |
| --- | --- |
| Exactly one directory directly under GameData | `find: <that directory>` |
| Several directories under GameData, one matching the identifier | `find: <identifier>` |
| Several directories under GameData, none matching | `find: ''` |
| No GameData; identifier-named folder exists anywhere | `find: <identifier>` |
| No GameData or identifier match; exactly one root folder | That root folder |
| No usable selection | `find: ''` |

Additional processing:

1. Add `filter` entries for `__MACOSX`, `.DS_Store`, `Thumbs.db`, `.git`, and
   `.gitignore` when present.
2. Add `filter_regexp` entries for `\.mdb$`, `\.pdb$`, `~$`, and `\.craft$`
   when present.
3. Give each `.craft` with `type = VAB|SPH` a separate `file: <path>` stanza
   targeting `Ships/VAB|SPH`; skip subassemblies.
4. Omit a sole stanza that equals the default (`find: <identifier>` to GameData).

Review implications:

- Empty `find` means manual review is required. Choose the intended folders,
  exclude bundled dependencies, declare their relationships, and consider whether
  the identifier should match the main folder.
- A matching mod folder can cause bundled folders to be excluded automatically,
  while leaving their dependencies undeclared. Check both decisions.
- Wrapper folders, versioned paths, or a broad `find: GameData` are fragile.
  Select stable inner folders. Preserve stable author namespaces under
  INSTALL-NAMESPACE.
- `Extras`, `Optional`, `Patches for X`, `Source`, and `Ships` can be included or
  omitted accidentally. Compare the selected files with the intended content.
- Craft heuristics do not replace the contract-prop exception in INSTALL-CONTENT.

## BOT-MARKER: What `x_via` means

`x_via: Automated SpaceDock CKAN submission` is informational. It can stay.

## HUMAN-PR: Common shapes of handwritten submissions

Human submissions often come from the metadata webtool (JSON,
`spec_version: v1.x`, many fields filled in) or handwritten YAML. Check for:

- Copies of host-provided `name`, `abstract`, `author`, `version`, and `download`
  that stop tracking upstream changes.
- Hard-coded `ksp_version`, release-specific `file:` paths, and missing `$vref`.
- Free-text licenses, identifiers containing underscores or unnecessary title
  text, and relationships using display names instead of CKAN identifiers.

Apply the same review rules to human and bot submissions.
