# CKAN / NetKAN spec cheat-sheet (KSP1)

Condensed from https://github.com/KSP-CKAN/CKAN/blob/master/Spec.md, `CKAN.schema`,
`NetKAN.schema`, and `Netkan/Transformers/*.cs` in `KSP-CKAN/CKAN`.
Use this to validate field values and to recognise fields that do not belong in a netkan.

## Contents
- What a `.netkan` is (files, YAML/JSON, multi-document files)
- Mandatory fields: identifier, version, license (full list), install, compatibility, relationships,
  resources, tags, other fields
- Bot-generated fields: computed during inflation, never hand-written
- NetKAN-only fields: `$kref` hosts, `$vref`, version and staging controls, internal `.ckan` files

## What a `.netkan` is

A `.netkan` is a *template*. The bot "inflates" it into one `.ckan` per release by filling in
fields from the host named in `$kref`. Anything set explicitly in the netkan overrides what the
host would provide, and therefore stops tracking upstream changes. That is why reviewers strip
fields the host can supply (name, abstract, author, homepage, repository, version, download,
ksp_version) unless there is a reason to pin them.

- Files live in `NetKAN/<identifier>.netkan`. The filename stem MUST equal `identifier` (CI error otherwise).
- `NetKAN/<identifier>.frozen` is a retired netkan (bot ignores it). Adding a `.netkan` while a
  `.frozen` of the same name exists is a CI error ("is frozen, unfreeze it by renaming or deleting").
- YAML is preferred for new files; JSON is accepted. Never mix both syntaxes in one file.
  In YAML, `$kref`/`$vref` values start with `#`, so they must be quoted: `$kref: '#/ckan/spacedock/1234'`.
- A file may hold several documents (`---` separators in YAML, or consecutive `{}` objects in JSON),
  one per host. Each document needs its own `identifier` and `$kref`. Each document is inflated
  and validated independently; results with equal `version` strings are then JSON-merged into one
  `.ckan` (properties union, later document's arrays replace earlier ones) with a `download`
  array. Therefore `$vref`, `x_netkan_version_edit`/`epoch`/`force_v`, `license` (when the host
  cannot supply it) and `install` (when ZIP layouts differ) are applied per document and should
  be repeated in every document ("Vref in both sections" is a recurring post-merge fix), while
  tags/relationships/name may sit in one document. A `$vref` in only one document still yields
  `ksp_version` in the merged result (union of properties) as long as that host's ZIP has the
  `.version`; CI does not flag the omission, so it is a SHOULD-FIX convention, not an error.
  Different version strings per host ("Generated 2 modules but only 1 requested") are a FATAL
  error.
- Only ONE `$kref` and ONE `$vref` per document.

## Mandatory fields of the inflated `.ckan`

`spec_version`, `identifier`, `name`, `abstract`, `author`, `license`, `version` (+ `download`
unless `kind` is `metapackage`/`dlc`). In a netkan, only `identifier` is required because the
`$kref` host provides the rest. A netkan that sets `license` explicitly must use a value from the
license list below. Metanetkans (`#/ckan/netkan/...`) skip license validation at the outer layer.

### identifier
- Pattern `^[A-Za-z0-9][A-Za-z0-9-]+$` (letters, digits, dashes; no underscores, spaces, dots).
- Case-sensitive for machines but MUST be unique case-insensitively across the whole repo.
- Should match the folder installed into `GameData` (then the default install stanza works and
  CKAN can detect manual installs), or for plugins the DLL name minus version/`.dll`. Prefer
  whichever is less likely to change. Strip version numbers, "KSP", "1.12", "[WIP]", release
  status, acronym suffixes, host names, and author names.
- The SpaceDock bot derives it from the SpaceDock mod *name* with all non-alphanumerics removed
  (`re.sub(r'[\W_]+', '', name)`), e.g. "Almajara: A galactic adventure: Core" ->
  `AlmajaraAgalacticadventureCore`. These almost always need pruning to the core name.

### version
- Format `[epoch:]mod_version`. Debian-style comparison, digit runs compared numerically,
  letters sort before non-letters. `1.10` > `1.9`. Epoch (`x_netkan_epoch`) resets ordering when
  the scheme changes; the bot auto-increments epoch when a release sorts below the previous one
  unless `x_netkan_allow_out_of_order: true`.
- Convention: version strings should NOT carry a leading `v`. GitHub tags like `v1.2.3` are cleaned
  with `x_netkan_version_edit: ^v?(?<version>.+)$` (regex must have a named group `version`; C#
  syntax `(?<name>...)`). Once a mod has been indexed WITH a `v`, keep it consistent
  (`x_netkan_force_v: true`) rather than switching, because `v1.2` sorts above `1.3`.
- SpaceDock versions are the uploader's free-text "friendly_version"; watch for `v`, spaces,
  dates, or words like "beta" that will sort wrongly.

### license
Must be one of (from `CKAN.schema`):
`public-domain, AFL-3.0, AGPL-3.0, Apache, Apache-1.0, Apache-2.0, APSL-2.0, Artistic, Artistic-1.0, Artistic-2.0, BSD-2-clause, BSD-3-clause, BSD-4-clause, ISC, CC-BY, CC-BY-1.0, CC-BY-2.0, CC-BY-2.5, CC-BY-3.0, CC-BY-4.0, CC-BY-SA, CC-BY-SA-1.0, CC-BY-SA-2.0, CC-BY-SA-2.5, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-BY-NC, CC-BY-NC-1.0, CC-BY-NC-2.0, CC-BY-NC-2.5, CC-BY-NC-3.0, CC-BY-NC-4.0, CC-BY-NC-SA, CC-BY-NC-SA-1.0, CC-BY-NC-SA-2.0, CC-BY-NC-SA-2.5, CC-BY-NC-SA-3.0, CC-BY-NC-SA-4.0, CC-BY-NC-ND, CC-BY-NC-ND-1.0, CC-BY-NC-ND-2.0, CC-BY-NC-ND-2.5, CC-BY-NC-ND-3.0, CC-BY-NC-ND-4.0, CC-BY-ND, CC-BY-ND-1.0, CC-BY-ND-2.0, CC-BY-ND-2.5, CC-BY-ND-3.0, CC-BY-ND-4.0, CC0, CDDL, CPL, EFL-1.0, EFL-2.0, Expat, MIT, GPL-1.0, GPL-2.0, GPL-3.0, LGPL-2.0, LGPL-2.1, LGPL-3.0, GFDL-1.0, GFDL-1.1, GFDL-1.2, GFDL-1.3, GFDL-NIV-1.0, GFDL-NIV-1.1, GFDL-NIV-1.2, GFDL-NIV-1.3, LPPL-1.0, LPPL-1.1, LPPL-1.2, LPPL-1.3c, MPL-1.0, MPL-1.1, MPL-2.0, Ms-PL, Ms-RL, Perl, Python-2.0, QPL-1.0, Unlicense, W3C, WTFPL, Zlib, Zope, open-source, restricted, unrestricted, unknown`
- May be an array when the user may choose (`[MIT, GPL-3.0]`). If different assets have different
  licenses, use the MOST restrictive one (often `restricted`). "All rights reserved" -> `restricted`.
- SpaceDock supplies a free-text license (e.g. `CC BY-NC-ND 4.0`, `MIT (configs)/ARR (assets)`);
  the bot normalises spaces to dashes, which frequently produces an invalid string and a CI FATAL
  "The licence X is invalid". Fix by setting a valid `license` in the netkan.
- GitHub `$kref` fills `license` from the repo's detected license (spec v1.26+). `x_netkan_license_ok: true`
  is an internal marker used on some metanetkans; it is not in the spec and should not be added casually.
- The license must match what is actually in the ZIP / forum thread, not just what the host says.

### install
Each stanza has exactly one source (`file`, `find`, `find_regexp`) and an `install_to`.
- `find: Foo` locates the top-most directory named `Foo` anywhere in the ZIP (preferred; robust to
  the author changing the wrapper folder). `file: path/in/zip` is an exact path (fragile).
  `find_regexp` is a C# regex over normalised paths (use sparingly).
- `install_to` for KSP1: `GameData`, `GameData/<subpath>`, `Ships`, `Ships/SPH`, `Ships/VAB`,
  `Ships/@thumbs/VAB`, `Ships/@thumbs/SPH`, `Ships/Script`, `Missions`, `Tutorial`, `Scenarios`,
  `GameRoot` (avoid). Craft files meant for the player to fly belong under `Ships/...`, not
  `GameData` (CI warns otherwise) - see `CST100Starliner.netkan`'s `find_regexp: ".*\\.craft$"` +
  `find_matches_files: true` pattern. **Exception:** a craft that is a contract/mission prop (a
  wreck, a rescue target) rather than something the player launches must stay inside the mod's own
  `GameData/<Id>/...`, at whatever path the mod's `.cfg` hardcodes - e.g. Contract Configurator's
  `SpawnVessel` behaviour reads `craftURL = <Id>/Assets/Ships/Foo.craft` relative to `GameData`.
  Moving such a craft into `Ships/` to quiet the "Craft files installed outside Ships folder"
  warning breaks the contract and wrongly exposes the prop as a launchable design. Check the ZIP's
  `.cfg` files for a `craftURL`/similar reference to the craft's filename before relocating it.
- Modifiers: `as` (rename), `filter` / `filter_regexp` (exclude), `include_only` /
  `include_only_regexp` (whitelist; cannot be combined with `filter*`), `find_matches_files: true`
  (let `find`/`find_regexp` match files too).
- **Default stanza** when `install` is omitted: `find: <identifier>` -> `GameData`. If the ZIP's
  GameData folder is named exactly like the identifier, DELETE the explicit stanza (reviewers do
  this routinely: "Use default install stanza").
- `find: ''` (empty) is the SpaceDock bot's signal that it could not pick a folder (several folders
  under GameData, none named like the identifier). It is never correct; a human must decide.
- Never install a bundled third-party mod (ModuleManager, Kopernicus, B9PartSwitch, MiniAVC folder
  copies, ...). Use `depends` and let CKAN install the real thing; installing copies causes file
  conflicts for users. Filter them out if the stanza would otherwise sweep them in.
- Installing this mod's OWN files into another indexed mod's folder (`find: TUFX`, `install_to:
  GameData/Kopernicus/...`) is a different case from bundling a copy, but still needs scrutiny:
  any path the target mod itself ships is a BLOCKER, since CKAN cannot overwrite another mod's
  files (wiki "Help! I need to overwrite another mod's files"). A uniquely-named add-on file
  (profile, patch) that cannot collide is survivable, but check real precedent before calling it
  OK — most frameworks that load drop-in configs (TUFX profiles, MM patches) scan all of
  `GameData`, so the file usually does not need to live inside the target's own directory at all;
  prefer the mod's own folder unless sibling netkans that install into that same folder (not just
  `depends` on the mod) show it is the accepted pattern.
- CI errors on: nothing matched, `GameData` nested inside `GameData`, two stanzas writing the same
  destination, `include_only` with no matches (warning), path traversal.

### Compatibility
- `ksp_version` (exact or 2-part prefix) XOR (`ksp_version_min` / `ksp_version_max`). `any` = unbounded.
- `ksp_version_strict: true` disables the client's "generally recognised as compatible" fuzzing.
- SpaceDock supplies `ksp_version` from the uploader's chosen game version; a `.version` file
  (`$vref: '#/ckan/ksp-avc'`) supplies min/max and wins for the range. Hard-coding compatibility
  in the netkan freezes it forever; prefer the host or the `.version` file.
- CI errors if the module matches no known game version; CI warns when a plugin mod has unbounded
  future compatibility (no `$vref`, `ksp_version`, or `ksp_version_max`).

### Relationships
`depends`, `recommends`, `suggests`, `supports`, `conflicts`; each an array of `{name: <identifier>}`
with optional `min_version`/`max_version` or `version` (not both). `any_of: [...]` for alternatives.
`replaced_by` is a single object, not an array. `provides: [ids]` declares virtual identifiers.
- `name` must be an existing CKAN identifier (exact case). Wrong case, a display name, or a folder
  name are CI errors only if syntactically invalid; a non-existent but valid-looking identifier
  passes CI and breaks installs. Verify against `NetKAN/` (+ `provides`) or CKAN-meta.
- `depends` = required to function. Debian-style semantics for the rest, and default to
  `suggests`: `recommends` = "you would not normally install this without also installing the
  target" (near-mandatory, resolver installs it by default); `suggests` = "consider also
  installing the target" (optional enhancement/integration — where most companion mods belong);
  `supports` = reverse of `suggests`; `conflicts` = cannot coexist. Use relationships only for a
  real gameplay/technical relationship, not promotion.
- Common must-haves: `ModuleManager` when any `.cfg` uses MM syntax (`@`, `+`, `!`, `%`, `$`, `-`,
  `NODE:NEEDS[...]`); `Kopernicus` for `@Kopernicus` planet packs; `Waterfall`, `B9PartSwitch`,
  `TUFX`, `ContractConfigurator`, `KerbalKonstructs` when their nodes/modules appear;
  `Harmony2` when a plugin references `0Harmony`; `Scatterer`/`EnvironmentalVisualEnhancements`
  for visual packs. Textures-only variants normally `depends` on the core mod.
- A `.version` file with `KSP_VERSION`, a `README` "requires X", or forum-thread text are the
  usual sources of truth for dependencies.
- If the mod overwrites files of another mod, it must instead be split or use MM; CKAN cannot
  overwrite (see wiki "Help! I need to overwrite another mod's files").

### resources
`homepage` (forum thread preferred), `bugtracker`, `discussions`, `license`, `repository`, `ci`,
`spacedock`, `curse`, `manual`, `metanetkan`, `remote-avc`, `remote-swinfo`, `store`, `steamstore`,
`gogstore`, `epicstore`, plus any `x_*`. SpaceDock and GitHub fill most of these; only set
`homepage` when the host's value is wrong or missing.

### tags
Lowercase `[a-z0-9-]+`. Use only the Suggested Tags vocabulary. Types: `parts`, `physics`,
`plugin`, `app`, `config`, `library`, `flags`, `agency`, `suits`. Descriptors: `control`,
`convenience`, `information`, `editor`, `planet-pack`, `graphics`, `sound`, `resources`,
`science`, `tech-tree`, `career`, `combat`, `comms`, `buildings`, `crewed`, `uncrewed`,
`stock-inventory`, `first-person`. CI only warns when tags are missing entirely; wrong or
made-up tags pass CI.

### Other fields
- `kind`: `package` (default) | `metapackage` (no download; relationships only) | `dlc`.
- `comment`: ignored, human notes. `x_*`: ignored extension fields.
- `localizations`: list of locale codes shipped; the bot fills this in from the ZIP's
  `Localization { ... }` cfg blocks (`LocalizationsTransformer`) whenever the property is absent,
  so hand-writing it only makes sense to override a bad auto-detection.

### Bot-generated fields (flag these if hand-written in a netkan)
Source: `KSP-CKAN/CKAN` `Netkan/Transformers/*.cs`, the pipeline `NetkanTransformer` runs in order
for every inflation. These are computed from the host response or the downloaded ZIP itself, not
from anything specific to one `$kref` host, so they don't belong in a netkan regardless of which
host it uses. A value found in a netkan is either silently discarded (unconditional overwrite) or
sticks and quietly stops tracking upstream (the transformer only fills a gap):
- `spec_version`: recomputed on every inflation from whichever spec features the merged metadata
  actually uses (`SpecVersionTransformer`, unconditional `json["spec_version"] = ...`). A
  hand-written value is simply replaced; harmless but always dead weight.
- `download_size`, `download_hash`, `download_content_type`, `install_size`: measured from the
  downloaded ZIP every inflation (`DownloadAttributeTransformer`, `InstallSizeTransformer`).
- `release_date`: taken from the host's API response for the matched release/asset (every host
  transformer sets it the same way).
- `release_status`: `stable` (default, i.e. absent) | `testing` | `development`. Only the GitHub
  and Gitea transformers ever set this automatically, to `testing`, and only for a release flagged
  as a prerelease on the host (`json.SafeAdd("release_status", "testing")` - `SafeAdd` means a
  value already in the netkan wins and is never touched again). Hand-writing `stable` is a no-op;
  hand-writing `testing` freezes that status even after the mod leaves prerelease; `development` is
  never set by the bot at all, so a netkan with `$kref` should not carry it either - drop it and
  let prerelease detection do its job (or ask the author to mark the GitHub release as a
  prerelease). The one legitimate use is a fully hand-authored file with no `$kref`, e.g.
  `Backports/Kopernicus.frozen`.
- `x_generated_by`: always unconditionally set to `"netkan"` (`GeneratedByTransformer`); any other
  value is discarded on the next inflation.
- `x_netkan_version_pieces`: internal bookkeeping the GitHub/Gitea transformers attach to the
  matched release tag (`{tag: <tag>}`); not meant to be hand-authored.

A netkan carrying any of these almost always means a hand-written file was copied from an already
inflated `.ckan` (or from another mod's netkan) instead of started fresh - point at the source
transformer above and say to delete the field.

## NetKAN-only fields

### `$kref`
- `#/ckan/spacedock/<id>`: fills name, license, abstract, author, version, download, homepage,
  spacedock, repository, bugtracker, x_screenshot, ksp_version, release_date, release_status.
- `#/ckan/github/<user>/<repo>[/asset_match/<regex>|/version_from_asset/<regex>]`: fills name,
  license, abstract, author, version (from tag), download (first asset by default), repository,
  bugtracker, release_date, release_status (prerelease -> testing). `x_netkan_github:
  {use_source_archive: true}` downloads GitHub's automatic source zip instead of an asset; that
  zip is a repository snapshot wrapped in `<repo>-<sha>/`, which normally does not have a mod
  install layout, so it only works when the repo root holds the mod folder and the install
  stanza uses `find`. Precedent (2026-09): 11 of 1456 live netkans use it (6 are one author's
  `RecolorCollection-*` packs); 10 of the 11 `find` the inner folder (`find: TU_MissingHistory`,
  `find_regexp: EmbeddedKOSKirkuits-.*`) and one relies on the default `find: <identifier>`.
  Accept it on that pattern; a release without assets and without it crashes inflation.
  `prereleases: true|false` filters releases.
  `asset_match` is needed when a release ships several assets (e.g. separate zips per game or a
  `.sha256` alongside the zip is fine because only `.zip`-like assets are considered, but two zips
  are ambiguous).
- `#/ckan/gitlab/<user>/<repo>` (needs `x_netkan_gitlab: {use_source_archive: true}`),
  `#/ckan/gitea/<host>/<user>/<repo>`, `#/ckan/sourceforge/<repo>`, `#/ckan/jenkins/<joburl>`
  (+`x_netkan_jenkins`), `#/ckan/http/<url>` (needs a `.version` file for the version),
  `#/ckan/ksp-avc/<url to .version>` (download from the file's `DOWNLOAD`).
- `#/ckan/netkan/<url>`: metanetkan; the remote file is authoritative and may not itself be a
  metanetkan. Fields in the local file override the remote. Used when authors want to own their
  metadata; for a single mod an internal `.ckan` inside the ZIP is the simpler alternative.
- A netkan with both `$kref` and `download` is a CI error; a netkan with neither is a CI error.

### `$vref`
- `#/ckan/ksp-avc[/path/to/file.version]`: read min/max game version (and `version` only when the
  host gave none, or when `x_netkan_trust_version_file: true`) from the `.version` file that would
  be installed. More than one candidate `.version` file is an error ("Too many .version files");
  disambiguate with the path suffix. CI warns if `$vref` is set but no `.version` exists, and if
  a `.version` exists but `$vref` is missing.
- `#/ckan/space-warp[/path]`: KSP2 only (`swinfo.json`); a KSP1 netkan with swinfo is wrong repo.

### Version and staging controls
- `x_netkan_version_edit`: string regex (must contain `(?<version>...)`) or
  `{find, replace: '${version}', strict: true}`. Strip `v`, dates, suffixes; `strict: false` if
  some tags will not match.
- `x_netkan_epoch: <int>`, `x_netkan_force_v: true`, `x_netkan_allow_out_of_order: true`,
  `x_netkan_trust_version_file: true`.
- `x_netkan_override: [{version: '>=1.0', override: {...}, delete: [...]}]` for version-specific
  metadata (preferred over editing old `.ckan`s). Needs `version` and one of `override`/`delete`.
- `x_netkan_staging: true` + `x_netkan_staging_reason: '...'` routes bot updates through a PR.

### Internal `.ckan` files
A `.ckan` (JSON or YAML) inside the ZIP is merged into that version's metadata. It can only ADD
properties, not override the netkan. Good for per-version dependencies; the netkan should then
omit those fields. More than one `.ckan` in a ZIP is an error.
