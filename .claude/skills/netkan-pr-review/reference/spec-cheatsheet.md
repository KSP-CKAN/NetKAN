# CKAN and NetKAN field reference for KSP1

Use this file for field syntax, allowed values, and inflation behavior. Use
[Review rules](review-rules.md) for review decisions and exceptions, and
[SKILL.md](../SKILL.md) for severity and verdicts.

Sources: [CKAN Spec.md](https://github.com/KSP-CKAN/CKAN/blob/master/Spec.md),
`CKAN.schema`, `NetKAN.schema`, and `Netkan/Transformers/*.cs` in `KSP-CKAN/CKAN`.
This is a condensed reference, not a copy of the full specification.

When editing, keep syntax separate from house conventions. Keep one license per
line in the vocabulary block and one generated field or field group per table row.

## Contents

- [Templates and file identity](#templates-and-file-identity)
- [Multiple host documents](#multiple-host-documents)
- [Required generated metadata](#required-generated-metadata)
- [Release fields](#release-fields): identifier, version, license, install,
  compatibility, relationships, resources, tags, other fields
- [Bot-generated fields](#bot-generated-fields)
- [NetKAN-only fields](#netkan-only-fields): `$kref`, `$vref`, version and staging
  controls, internal `.ckan`

## Templates and file identity

A `.netkan` is a template. Inflation creates one `.ckan` per release by filling
in fields from the `$kref` host. Explicit template values override host values
and stop tracking their changes. Avoid redundant `name`, `abstract`, `author`,
homepage, repository, version, download, and compatibility fields unless a pin
or override is justified.

| Item | Requirement |
| --- | --- |
| Location | `NetKAN/<identifier>.netkan` |
| Filename | Stem equals `identifier`; otherwise CI fails. |
| Frozen entry | `NetKAN/<identifier>.frozen` is ignored by the bot. A same-named live and frozen entry fails CI: "is frozen, unfreeze it by renaming or deleting". |
| Format | YAML preferred; JSON accepted. Do not mix syntaxes in one file. |
| References in YAML | Quote `$kref` / `$vref` values beginning with `#`, e.g. `$kref: '#/ckan/spacedock/1234'`. |

## Multiple host documents

Use `---` between YAML documents, or consecutive JSON objects. Each host
document needs its own identifier and `$kref`. Allow at most one `$kref` and
one `$vref` per document.

Inflation proceeds as follows:

1. Inflate and validate each document independently.
2. Merge results with identical version strings into one `.ckan`.
3. Union properties; later arrays replace earlier arrays. Collect host downloads
   in the `download` array.

Different host version strings cause a FATAL such as "Generated 2 modules but
only 1 requested".

Fields processed before merging must be supplied in every applicable document:
`$vref`, `x_netkan_version_edit`, `x_netkan_epoch`, `x_netkan_force_v`, `license`
when the host cannot supply it, and `install` when ZIP layouts differ. Shared
tags, relationships, and name can live in one document.

A `$vref` in one document can still provide compatibility to the merged result
when that ZIP contains the version file. Repeating it in both documents is the
house convention (HOST-FIELDS), not an independent CI requirement.

## Required generated metadata

An inflated `.ckan` needs `spec_version`, `identifier`, `name`, `abstract`,
`author`, `license`, and `version`. It also needs `download` unless its `kind`
is `metapackage` or `dlc`.

Do not copy that whole set into a netkan: inflation supplies most of it. The
netkan identifies the mod and its source, then supplies whatever the host cannot.
If `license` is explicit, use the vocabulary below. Metanetkans skip license
validation at the outer layer.

## Release fields

### identifier

| Aspect | Rule |
| --- | --- |
| Syntax | `^[A-Za-z0-9][A-Za-z0-9-]+$`; letters, digits, dashes; no underscores, spaces, or dots. |
| Uniqueness | Case-sensitive in metadata; unique case-insensitively across the repository. |
| Preferred name | Stable GameData folder or plugin DLL base name, without `.dll` or version text. This supports default installs and manual-install detection. |
| Title cleanup | Remove versions, KSP/game-version text, WIP/release status, extraneous acronym suffixes, host/author names, and subtitles. Apply ID-NAME and ID-INSTALL, including documented reasons for a mismatch. |

The SpaceDock bot uses `re.sub(r'[\W_]+', '', name)`. For example,
"Almajara: A galactic adventure: Core" becomes
`AlmajaraAgalacticadventureCore`; review the result rather than accepting the
whole title as the identifier.

### version

The format is `[epoch:]mod_version`. Comparison is Debian-style: digit runs
compare numerically (`1.10` > `1.9`), and letters sort before non-letters.

| Situation | Behavior or control |
| --- | --- |
| Version scheme changes | Epoch resets ordering. The bot automatically increments it for a release sorting below the previous one, unless `x_netkan_allow_out_of_order: true`. |
| Explicit epoch floor | `x_netkan_epoch` |
| Host strings differ | Normalize consistently with `x_netkan_version_edit`; the regex needs C# named capture `(?<version>...)`. |
| Already indexed with `v` | Preserve it with `x_netkan_force_v: true`; `v1.2` sorts above `1.3`. |
| SpaceDock friendly version | Free text; check prefixes, spaces, dates, and words such as beta for unintended ordering. |

Stripping `v` with `^v?(?<version>.+)$` is a common convention, not a reason on
its own to request a correction. VERSION-MATCH accepts a prefix shared by every
host. Do not normalize an already-consistent release merely for style.

### license

Use an exact value from this `CKAN.schema` vocabulary:

```text
public-domain
AFL-3.0
AGPL-3.0
Apache
Apache-1.0
Apache-2.0
APSL-2.0
Artistic
Artistic-1.0
Artistic-2.0
BSD-2-clause
BSD-3-clause
BSD-4-clause
ISC
CC-BY
CC-BY-1.0
CC-BY-2.0
CC-BY-2.5
CC-BY-3.0
CC-BY-4.0
CC-BY-SA
CC-BY-SA-1.0
CC-BY-SA-2.0
CC-BY-SA-2.5
CC-BY-SA-3.0
CC-BY-SA-4.0
CC-BY-NC
CC-BY-NC-1.0
CC-BY-NC-2.0
CC-BY-NC-2.5
CC-BY-NC-3.0
CC-BY-NC-4.0
CC-BY-NC-SA
CC-BY-NC-SA-1.0
CC-BY-NC-SA-2.0
CC-BY-NC-SA-2.5
CC-BY-NC-SA-3.0
CC-BY-NC-SA-4.0
CC-BY-NC-ND
CC-BY-NC-ND-1.0
CC-BY-NC-ND-2.0
CC-BY-NC-ND-2.5
CC-BY-NC-ND-3.0
CC-BY-NC-ND-4.0
CC-BY-ND
CC-BY-ND-1.0
CC-BY-ND-2.0
CC-BY-ND-2.5
CC-BY-ND-3.0
CC-BY-ND-4.0
CC0
CDDL
CPL
EFL-1.0
EFL-2.0
Expat
MIT
GPL-1.0
GPL-2.0
GPL-3.0
LGPL-2.0
LGPL-2.1
LGPL-3.0
GFDL-1.0
GFDL-1.1
GFDL-1.2
GFDL-1.3
GFDL-NIV-1.0
GFDL-NIV-1.1
GFDL-NIV-1.2
GFDL-NIV-1.3
LPPL-1.0
LPPL-1.1
LPPL-1.2
LPPL-1.3c
MPL-1.0
MPL-1.1
MPL-2.0
Ms-PL
Ms-RL
Perl
Python-2.0
QPL-1.0
Unlicense
W3C
WTFPL
Zlib
Zope
open-source
restricted
unrestricted
unknown
```

| Licensing situation | Metadata treatment |
| --- | --- |
| User may choose between licenses | An array is allowed, e.g. `[MIT, GPL-3.0]`. |
| Different assets have different licenses | Use the most restrictive applicable value, often `restricted`. |
| All rights reserved | `restricted` |
| Genuinely unknown | `unknown` |

Compare the ZIP and forum evidence with the host's declared license. A valid
host string does not prove that it matches the distributed content.

SpaceDock supplies free text and the bot normalizes spaces to dashes. Values
such as `CC BY-NC-ND 4.0` or `MIT (configs)/ARR (assets)` may still be invalid and
produce "The licence X is invalid". Supply a valid override where needed.

GitHub supplies its detected repository license (spec v1.26+). Avoid a redundant
override when detection is correct. `x_netkan_license_ok: true` is an internal
marker on some metanetkans, not a spec field to add casually.

### install

Each stanza has exactly one source and an `install_to`:

| Source | Meaning |
| --- | --- |
| `find: Foo` | Find the topmost directory named Foo anywhere in the ZIP. Preferred for resilience to wrapper-folder changes. |
| `file: path/in/zip` | Exact path; vulnerable to release-specific layout changes. |
| `find_regexp` | C# regex over normalized ZIP paths; use sparingly. |

| Modifier | Meaning |
| --- | --- |
| `as` | Rename the selected content. |
| `filter` / `filter_regexp` | Exclude content. |
| `include_only` / `include_only_regexp` | Include only matching content; cannot combine with `filter*`. |
| `find_matches_files: true` | Permit `find` / `find_regexp` to select files as well as directories. |

Allowed KSP1 destinations:

```text
GameData
GameData/<subpath>
Ships
Ships/SPH
Ships/VAB
Ships/@thumbs/VAB
Ships/@thumbs/SPH
Ships/Script
Missions
Tutorial
Scenarios
GameRoot
```

Avoid GameRoot unless justified. Apply these selection and ownership checks:

- **Default install:** omitting `install` means `find: <identifier>` to GameData.
  Remove an explicit copy of the default when the identifier matches the sole
  GameData folder and no additional selection is needed.
- **Empty selection:** `find: ''` means the bot could not choose a folder. It is
  never a correct final selection; choose the intended content.
- **Bundled dependencies:** exclude their folders/DLLs and declare relationships
  so CKAN supplies the real mods. This includes ModuleManager, Kopernicus,
  B9PartSwitch, and separate MiniAVC folders.
- **Other mods' folders:** a path colliding with a file owned by another indexed
  mod is a BLOCKER. A uniquely named profile/patch still needs matching sibling
  precedent before acceptance. TUFX/MM drop-in files generally work from the
  add-on's own GameData folder. Check actual install paths, not just shared
  dependency declarations (INSTALL-OTHER-MOD).
- **Shared author namespace:** preserve its on-disk layout while selecting only
  this mod's inner folder; put the namespace in `install_to` (INSTALL-NAMESPACE).

Craft files require a purpose check:

| Craft purpose | Install treatment |
| --- | --- |
| Player-launchable design | Ships destination. `CST100Starliner.netkan` demonstrates `find_regexp: ".*\\.craft$"` plus `find_matches_files: true`. |
| Contract/mission prop | Keep its referenced GameData path. `SpawnVessel` can use `craftURL = <Id>/Assets/Ships/Foo.craft` relative to GameData. |

Search CFGs for the filename and `craftURL` before moving a craft. Moving a prop
to Ships breaks its reference and exposes a design the player was not meant to
launch. The CI craft-location warning does not override this exception.

CI rejects unmatched sources, GameData nested inside GameData, duplicate
destinations, and path traversal. An unmatched `include_only` produces a warning.

### Compatibility

Use either `ksp_version` (an exact version or two-part prefix) or a range using
`ksp_version_min` / `ksp_version_max`, not both forms. `any` means unbounded.
`ksp_version_strict: true` disables the client's generally-recognized-compatible
version fuzzing.

SpaceDock supplies the uploader's selected game version. An installed `.version`
selected by `$vref: '#/ckan/ksp-avc'` supplies compatibility and takes precedence
for the range. Avoid a static override when either source supplies it.

CI errors when no known game version matches. It warns on unbounded future
compatibility for plugin mods without `$vref`, `ksp_version`, or `ksp_version_max`.

### Relationships

`depends`, `recommends`, `suggests`, `supports`, and `conflicts` are arrays of
objects containing `name: <identifier>`. An entry can constrain
`min_version` / `max_version` or use `version`, but not both forms.
Use `any_of: [...]` for alternatives. `replaced_by` is a single object;
`provides: [ids]` declares virtual identifiers.

| Relationship | Meaning |
| --- | --- |
| `depends` | Required for this mod to function or have a purpose. |
| `recommends` | Near-mandatory in normal use; resolver installs it by default. |
| `suggests` | Optional enhancement/integration. Default for optional companions. |
| `supports` | Offer this mod when the target is installed; reverse of suggests. |
| `conflicts` | Cannot coexist. |

Use relationships for actual technical or gameplay connections, not promotion.
Apply REL-REQUIRED and REL-OPTIONAL to distinguish them.

Check names against exact CKAN identifiers in `NetKAN/`, `provides`, or CKAN-meta.
Display names, folder names, and wrong case may be syntactically valid and escape
inflation checks; required targets can then fail the sandbox install, while
optional names can silently do nothing.

Dependency clues include MM syntax (`@`, `+`, `!`, `%`, `$`, `-`,
`NODE:NEEDS[...]`), `@Kopernicus`, framework modules for Waterfall/B9PartSwitch/
TUFX/ContractConfigurator/KerbalKonstructs, plugin references to `0Harmony`
(`Harmony2`), and Scatterer/EVE visual content. Textures-only variants normally
need their core mod. Read the README, forum, and version-file context too.
Interpret optional patches and bridge DLLs under 3h rather than treating every
framework mention as mandatory.

CKAN cannot overwrite another mod's files. Propose patches or a module split
instead of trying to impose an install order.

### resources

Supported names include:

```text
homepage
bugtracker
discussions
license
repository
ci
spacedock
curse
manual
metanetkan
remote-avc
remote-swinfo
store
steamstore
gogstore
epicstore
x_*
```

Hosts fill most resources. Prefer the forum thread for homepage; set an override
when the host value is missing or wrong.

### tags

Syntax is lowercase `[a-z0-9-]+`. Use the Suggested Tags vocabulary in
[Wiki guidance](doc-checklist.md#doc-tags-accepted-vocabulary), which separates
types from descriptors. CI warns on absent tags, not invented or unsuitable ones.

### Other fields

| Field | Meaning |
| --- | --- |
| `kind` | `package` by default; `metapackage` for relationships without a download; `dlc` for DLC. |
| `comment` | Human notes, ignored by processing. |
| `x_*` | Extension fields, ignored unless a transformer recognizes them. |
| `localizations` | Shipped locale codes. `LocalizationsTransformer` detects these from `Localization { ... }` CFG blocks when absent; override only to correct detection. |

## Bot-generated fields

These come from host responses or ZIP analysis during inflation. A handwritten
value is either replaced or prevents future updates when a transformer only
fills missing values. Remove them from ordinary `$kref` templates
(META-GENERATED).

| Field | Producer and behavior |
| --- | --- |
| `spec_version` | `SpecVersionTransformer` recomputes it from the features used; unconditionally replaces a handwritten value. |
| `download_size`, `download_hash`, `download_content_type` | `DownloadAttributeTransformer` measures the downloaded archive each inflation. |
| `install_size` | `InstallSizeTransformer` measures installed content. |
| `release_date` | Host transformer supplies the matched release/asset date. |
| `release_status` | Default stable is represented by absence. GitHub/Gitea use `SafeAdd` to set testing for prereleases; an existing template value wins and can become stale. |
| `x_generated_by` | `GeneratedByTransformer` unconditionally sets netkan. |
| `x_netkan_version_pieces` | GitHub/Gitea bookkeeping for the matched tag, such as `{tag: <tag>}`. |

For `release_status`, writing stable adds nothing; writing testing keeps it even
after prerelease ends. The bot never generates development. Prefer host
prerelease flags to a fixed status. A fully hand-authored file without `$kref`,
such as `Backports/Kopernicus.frozen`, is the documented exception.

These fields often indicate a copied inflated `.ckan`. Explain the relevant
producer and propose deleting the field rather than maintaining a stale copy.

## NetKAN-only fields

### `$kref`

| Reference | Source and options |
| --- | --- |
| `#/ckan/spacedock/<id>` | Supplies display fields, license, version, download, homepage, SpaceDock/repository/bugtracker links, `x_screenshot`, compatibility, release date, and applicable status metadata. |
| `#/ckan/github/<user>/<repo>[/asset_match/<regex>\|/version_from_asset/<regex>]` | Supplies display fields, detected license, tag version, download, repository/bugtracker, release date, and prerelease status. |
| `#/ckan/gitlab/<user>/<repo>` | Requires `x_netkan_gitlab: {use_source_archive: true}`. |
| `#/ckan/gitea/<host>/<user>/<repo>` | Gitea/Forgejo host. |
| `#/ckan/sourceforge/<repo>` | SourceForge. |
| `#/ckan/jenkins/<joburl>` | Jenkins; configure `x_netkan_jenkins` as needed. |
| `#/ckan/http/<url>` | Plain HTTP download; requires a `.version` file to supply the version. |
| `#/ckan/ksp-avc/<url to .version>` | Uses the version file's `DOWNLOAD`. |
| `#/ckan/netkan/<url>` | Remote authoritative template; local fields override it. Remote template must not itself be a metanetkan. |

For GitHub releases:

- Default selection takes the first eligible asset. Use `asset_match` when
  several ZIP-like assets are ambiguous; a `.sha256` alongside one ZIP is fine.
- `prereleases: true|false` filters release selection.
- `x_netkan_github: {use_source_archive: true}` selects the automatic source
  archive wrapped in `<repo>-<sha>/`. Accept it only when it contains the mod's
  folder and a stable `find` selects that content. Without a usable asset or
  this option, a release with no assets fails inflation.
- In the September 2026 sample, 11 of 1456 live netkans used source archives;
  six were one author's `RecolorCollection-*` packs. Ten explicitly selected
  inner content (such as `find: TU_MissingHistory` or
  `find_regexp: EmbeddedKOSKirkuits-.*`), and one used default identifier matching.
  This is historical precedent, not a requirement to mimic those files.

A document with both `$kref` and `download`, or neither, fails CI. Fully manual
metadata is a distinct workflow; do not copy its fields into a host template.
For one mod, an internal `.ckan` can be simpler than a remote metanetkan.

### `$vref`

| Reference | Behavior |
| --- | --- |
| `#/ckan/ksp-avc[/path/to/file.version]` | Reads game compatibility from the installed version file. Supplies the mod version only when the host has none, or `x_netkan_trust_version_file: true`. |
| `#/ckan/space-warp[/path]` | KSP2 `swinfo.json`; outside this KSP1 review. |

More than one candidate AVC file causes "Too many .version files"; use a path
suffix to disambiguate. CI warns both when `$vref` selects no version file and
when a version file exists without `$vref`.

### Version and staging controls

| Field | Syntax or purpose |
| --- | --- |
| `x_netkan_version_edit` | A regex containing `(?<version>...)`, or `{find, replace: '${version}', strict: true}`. Use `strict: false` when some tags may not match. |
| `x_netkan_epoch` | Integer epoch floor. |
| `x_netkan_force_v` | `true` preserves a required v prefix. |
| `x_netkan_allow_out_of_order` | `true` for intentional out-of-order releases. |
| `x_netkan_trust_version_file` | `true` to prefer the version file's mod version. |
| `x_netkan_override` | `[{version: '>=1.0', override: {...}, delete: [...]}]`; requires version and at least override or delete. Prefer this to editing old generated `.ckan` files. |
| `x_netkan_staging` / `x_netkan_staging_reason` | `true` plus an explanation routes bot updates through a PR. |

### Internal `.ckan` files

An installed JSON or YAML `.ckan` contributes release-specific properties but
does not override template values. Leave its fields out of the netkan when it
should supply them. More than one selected internal `.ckan` is an error; for
multi-module archives, separate install selections. See
[Uncommon cases](uncommon-cases.md#internal-ckan-metadata-shipped-in-the-zip).
