# Wiki guidance for NetKAN reviews

Use this reference for the documented checklist, tag vocabulary, labels, and
CKAN design constraints. [Review rules](review-rules.md) supplies the decisions
and exceptions used by this skill. [SKILL.md](../SKILL.md) defines verdicts.

Sources: CKAN wiki pages "How to Wrangle Metadata for KSP1", "Adding a mod to the
CKAN" (including "NetKAN review checklist" and "Internal .ckan files"),
"Suggested Tags", "Metadata labeling guide", and the CKAN opt-out policy.

When editing, keep vocabulary lists in their sections and distinguish reviewer
advice from technical requirements. Labels below are information for the report;
this skill does not apply labels or post requests to GitHub.

## DOC-GATES: Checks before metadata review

| Check | Requirement and evidence |
| --- | --- |
| Permission | The author or current maintainer must consent. A SpaceDock bot request counts only if the uploader is that author/maintainer; compare `author` / `shared_authors` with GitHub and the forum. Re-uploads need scrutiny. |
| CI | The Inflate check must pass before merge. If it has not run, a maintainer may need to approve it. If dependency compatibility is the obstacle, the PR-body directive `ckan compat add 1.10 1.11 1.12` can simulate user compatibility settings. |
| Game | KSP1 only: SpaceDock `game_id: 3102`, `.version` KSP 1.x, and no KSP2 `swinfo.json` / BepInEx payload. KSP2 belongs in KSP2-NetKAN. |
| Duplicates | Search live and frozen entries for the SpaceDock ID, repository, folders, DLLs, and similar names. Reconcile continued/revived forks and alternate hosts with existing entries. |

For third-party human PRs, approval should be quoted or linked in the body. If
it is missing there, look for it before declaring permission absent. Approval
found elsewhere passes the gate; request the link as a judgement call. See
GATE-PERMISSION for the full decision.

Authors on the [opt-out list](https://github.com/KSP-CKAN/CKAN/blob/master/policy/Opt-out-list.md)
must not be indexed or contacted.

For duplicate or fork cases, possible resolutions include multi-hosting the
existing netkan, `provides` / `replaced_by` / `conflicts`, or closing a duplicate.
Describe the applicable resolution; do not perform it during this review.

## DOC-CHECKLIST: The wiki's new-netkan checklist

- [ ] License is a valid spec value and matches the ZIP or forum evidence.
- [ ] Homepage points to the forum thread. SpaceDock's website supplies it
      automatically; override only when missing or wrong.
- [ ] `$vref` uses this mod's installed `.version` file. The wiki also covers
      KSP2 `swinfo.json`, but KSP2 submissions are outside this skill.
- [ ] Tags use Suggested Tags.
- [ ] Dependencies and conflicts are declared, and bundled dependencies are excluded.

## DOC-IDENTIFIER: Choose a useful identifier

Prefer the folder installed into GameData; for a plugin, prefer its DLL base
name. If the DLL and folder differ, choose the more stable name and encourage
upstream consistency. Matching names help CKAN detect manual installs.

Remove version information, release status, and extraneous title text from
SpaceDock-generated names. When the identifier matches the sole GameData folder
and the default install suffices, remove the explicit `install` stanza.

## DOC-STYLE: Metadata maintenance conventions

- Prefer YAML for new netkans.
- Let hosts supply fields such as `name`, `abstract`, `resources.homepage`, and
  `resources.repository`; avoid redundant overrides.
- Maintain tags using the vocabulary below.
- Exclude bundled dependencies and declare relationships instead.
- Recommend recording the reason for metadata changes in the PR body so future
  wranglers can find it.
- Raise unresolved questions rather than proposing changes that could break installs.

## DOC-TAGS: Accepted vocabulary

Ideally include at least one type. Descriptors are optional.

| Types | Descriptors |
| --- | --- |
| `parts`, `physics`, `plugin`, `app`, `config`, `library`, `flags`, `agency`, `suits` | `control`, `convenience`, `information`, `editor`, `planet-pack`, `graphics`, `sound`, `resources`, `science`, `tech-tree`, `career`, `combat`, `comms`, `buildings`, `crewed`, `uncrewed`, `stock-inventory`, `first-person` |

Tags are useful filter groups. Do not invent them or copy structural guesses
without checking what the mod does.

| Tag or content | Guidance |
| --- | --- |
| `config` | Alternative/default configurations, patches, or tech trees. Merely shipping CFGs does not make a parts mod a config mod. |
| `library` | Content that does nothing by itself. |
| `plugin` | Ships a DLL. |
| Kopernicus planet pack | `planet-pack` |
| Contract pack | `career` |
| IVAs | `crewed`, `first-person` |
| Visual pack | `graphics` |
| Autopilot | `control` |
| HUD | `information` |

## DOC-LABELS: Vocabulary used by wranglers

| Purpose | Labels |
| --- | --- |
| PR corrections | `Fix install`, `Fix license`, `Fix relationships` |
| Issues | `Mod-request`, `Mod-enhancement`, `Support` |
| Author/dependency blockers | `Blocked-on-mod-author`, `Blocked-on-dependency` |
| Tooling/host blockers | `Blocked-on-CKAN-feature`, `Blocked-on-other` |
| Discussion and triage | `Discussion needed`, `In progress`, `Needs looking into`, `Easy`, `Critical` |

An unindexed dependency can justify `Blocked-on-dependency`; a required file
overwrite can justify `Blocked-on-CKAN-feature`; an unsupported host can justify
`Blocked-on-other`. These label names do not replace the skill's verdict rules.

## DOC-CONSTRAINTS: Limits metadata cannot bypass

### File ownership

CKAN never overwrites another module's files and has no install order. A mod
that replaces another mod's files needs ModuleManager patches or separate modules
with appropriate `provides` / `conflicts` (the Scatterer-config pattern).
Metadata alone cannot make overwriting safe. Discuss repackaging or the relevant
`Blocked-on-CKAN-feature` / `Blocked-on-mod-author` label.

### Metadata maintained by the author

An internal `.ckan` can add properties, but cannot override values set by the
netkan. Leave those fields out of the netkan when the internal file should own them.

A metanetkan lets the author maintain metadata in their repository. For one mod,
an internal `.ckan` is usually simpler and keeps metadata versioned with releases.

### Archive format

The ZIP must extract with ordinary tools. Exotic compression fails in CKAN with
messages such as "Compression method not supported".
