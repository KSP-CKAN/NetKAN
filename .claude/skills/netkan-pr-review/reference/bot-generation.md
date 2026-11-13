# How SpaceDock bot PRs are generated (and where they go wrong)

Source: `KSP-CKAN/NetKAN-Infra` `netkan/spacedock_adder.py` and `netkan/mod_analyzer.py`.
When a SpaceDock uploader ticks "Add to CKAN", `netkan-bot` opens a PR titled
`Add <SpaceDock name> from SpaceDock` on branch `add/<identifier>` with label `Mod request`.
The PR body is the SpaceDock listing (name, authors, abstract, license, size, homepage, source).

## Identifier
`re.sub(r'[\W_]+', '', spacedock_name)`: the display name with everything non-alphanumeric
deleted. "Kerbal 3D Exporter" -> `Kerbal3DExporter` (fine); "Almajara: A galactic adventure:
Core" -> `AlmajaraAgalacticadventureCore` (needs pruning); "KH's Better Mun" -> `KHsBetterMun`;
"Star Strider | Stock-alike Crew Spacecraft" -> `StarStriderStockalikeCrewSpacecraft`.
The filename follows the identifier, so pruning the identifier means RENAMING the file in the PR.

## Documents produced
1. If the SpaceDock "source code" link is a GitHub repo with at least one release, a first YAML
   document with `$kref: '#/ckan/github/<user>/<repo>'`:
   - `x_netkan_github: {use_source_archive: true}` if the latest release has NO assets. Treat
     this as a guess to verify: the automatic source zip is a repository snapshot and usually
     lacks a mod install layout, so check the ZIP facts or drop the GitHub document.
   - `x_netkan_version_edit: '^<prefix>?(?<version>.+)$'` where `<prefix>` is whatever precedes
     the first digit of the latest tag (`v`, `V`, `release-`, ...). Only the LATEST tag is
     inspected, so mixed tag styles produce a regex that fails on older releases.
   - `$vref: '#/ckan/ksp-avc'` if the asset zip contains a `.version` file.
2. A SpaceDock document: `identifier`, `$kref: '#/ckan/spacedock/<id>'`, optional `$vref`, then
   the analyzer output, then `x_via: Automated SpaceDock CKAN submission`.
   The GitHub document does NOT get tags/depends/install (only the SpaceDock one does) so the
   inflated results differ per host until fixed. Reviewers usually keep both documents (multi-hosting
   gives users a fallback download) and make them consistent, or drop the GitHub one if it has no
   usable releases.

## Analyzer heuristics (what the tags/depends/install are based on)
Content regexes over `.cfg` files and filenames in the ZIP:

| Signal | tags | depends |
|---|---|---|
| any MM syntax (`^[@+$-!%]` or `^NAME:`) | | ModuleManager |
| `PART {` | parts (and removes `config`) | |
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
| `swinfo.json` | | SpaceWarp (KSP2!) |
| `*.dll` | plugin | |
| `*.cfg` | config | |
| `*.patch` | config | PatchManager |
| `/Spaces/` or `/Props/` | first-person | |

Consequences:
- Tags are purely structural. `config` is added for any cfg (even a single settings file) and
  `graphics` for any Waterfall module; gameplay tags (planet-pack, science, career, control,
  information, editor, convenience, resources, combat, comms, uncrewed, sound, flags, agency, suits,
  library, app, physics) are only added when a regex hits, so most bot PRs need tag curation.
- `depends` only covers the table above. Anything else (Firespitter, CommunityResourcePack,
  B9 wings, Scatterer, EVE, Parallax, ReStock, KSPCommunityFixes, ...) must come from the reviewer.
- ModuleManager is added even when the only MM syntax is in an optional/extras patch.

## Install stanza logic (`find_folder`)
1. If exactly one directory sits directly under `GameData` -> `find: <that dir>`.
2. If several sit under `GameData` -> `find: <identifier>` if one of them is named like the
   identifier, else `find: ''` (EMPTY: "manual review required").
3. No `GameData`: a folder named like the identifier anywhere -> `find: <identifier>`; else the
   single root folder if there is exactly one; else `find: ''`.
4. `filter` is added for `__MACOSX`, `.DS_Store`, `Thumbs.db`, `.git`, `.gitignore`;
   `filter_regexp` for `\.mdb$`, `\.pdb$`, `~$`, `\.craft$` when such files exist.
5. `.craft` files with `type = VAB|SPH` get one `file: <path>` stanza each into `Ships/VAB|SPH`
   (subassemblies are skipped).
6. If the only stanza equals the default (`find: <identifier>` -> `GameData`), it is omitted.

Consequences:
- `find: ''` always needs a human decision (which folders to install; whether some are bundled
  dependencies to be replaced by `depends`; whether the identifier should be renamed to the main
  folder).
- If `GameData/` holds the mod folder AND bundled dependencies (ModuleManager.dll, `000_Toolbar`,
  `Kopernicus`, ...), rule 2 picks `find: <identifier>` only when the folder already matches; the
  bundled dependencies are silently excluded (good) but not declared (bad).
- A `find` for a wrapper folder (`GameData` itself, a version-numbered folder, the mod name with
  spaces) will break when the author repacks. Prefer the innermost stable folder name.
- Extra folders shipped for optional use (`Extras`, `Optional`, `Patches for X`, `Source`,
  `Ships`) are either wrongly included or silently dropped depending on the rule that fired.

## `x_via`
`x_via: Automated SpaceDock CKAN submission` is informational; reviewers usually leave it.

## Typical human PRs
Human "Add X" PRs come from the metadata webtool (JSON, `spec_version: v1.x`, all fields filled)
or hand-written YAML. Common shapes: explicit `name`/`abstract`/`author`/`version`/`download`
copied from the release (should be removed so the host tracks updates), `ksp_version` hard-coded,
`install` using `file:` with a release-specific path, missing `$vref`, `license` copied as free
text, identifiers with underscores or lowercase, relationship names given as display names.
