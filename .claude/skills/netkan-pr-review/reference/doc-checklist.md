# Documented review rules (from the CKAN wiki)

Sources: wiki pages "How to Wrangle Metadata for KSP1", "Adding a mod to the CKAN" (incl. its
"NetKAN review checklist" and "Internal .ckan files"), "Suggested Tags", "Metadata labeling guide",
plus the CKAN `policy/Opt-out-list.md`.

## Gatekeeping (before looking at the metadata)
1. **Permission.** Do not add a mod without the author's (or current maintainer's) consent.
   - A SpaceDock bot PR counts as consent ONLY IF the SpaceDock uploader is the author. Check the
     SpaceDock author/shared_authors against the forum thread / GitHub owner. Re-uploads of other
     people's mods happen.
   - For human PRs by someone other than the author, the approval (forum post, Discord, issue)
     should be quoted/linked in the PR. If missing: label `Blocked-on-mod-author` and ask.
   - Authors on the opt-out list must not be indexed or contacted:
     https://github.com/KSP-CKAN/CKAN/blob/master/policy/Opt-out-list.md
2. **Green check required.** Never merge without the Inflate check passing. If the check has not
   run, it needs approval. If it fails because a dependency is not compatible with the same game
   versions, `ckan compat add 1.10 1.11 1.12` in the PR body simulates the user's compat settings.
3. **Right repo/game.** KSP1 only (`spacedock game_id` 3102, `.version` `KSP_VERSION` 1.x,
   no `swinfo.json`/BepInEx). KSP2 mods go to KSP2-NetKAN.
4. **Not a duplicate.** Search `NetKAN/` (and `.frozen`) for the same SpaceDock id, GitHub repo,
   folder name, DLL name, or a similar identifier/name. A re-upload of an existing mod, a
   "continued"/"revived" fork of an indexed mod, or a mod already indexed from another host must be
   reconciled (multi-host the existing netkan, add `provides`/`replaced_by`/`conflicts`, or close).

## The wiki's explicit review checklist for a new netkan
- [ ] **License** matches the license inside the ZIP or on the forum thread (valid spec string).
- [ ] **Homepage** points to the forum thread (SpaceDock's "website" is used automatically; only
      override when it is missing/wrong).
- [ ] **`$vref`** is set if the ZIP contains a `.version` file (KSP1) or `swinfo.json` (KSP2).
- [ ] **Tags** follow the Suggested Tags list.
- [ ] **Dependencies / conflicts** are declared (and bundled dependencies are NOT installed).

## Identifier rules (wiki "Make sure the identifier is good")
- Should match the folder installed into `GameData`; when it does, delete the `install` stanza and
  rely on the default.
- For a plugin, match the DLL name so CKAN can detect manual installs; if DLL and folder differ,
  pick the one less likely to change; encourage the author toward consistency.
- SpaceDock-derived identifiers contain "extraneous junk like version info, release status,
  acronyms": prune to the actual core name of the mod.

## Metadata best practices (wiki)
- New netkans in YAML.
- Let SpaceDock populate `name`, `abstract`, `resources.homepage`, `resources.repository` (do not
  hard-code them).
- Maintain `tags` per Suggested Tags.
- "Don't install bundled dependencies; add a `depends` clause instead."
- Put the reason for changes in the PR body so future wranglers can find it.
- If unsure, ask; "It's better to delay for a day or two than to break users' installs."

## Suggested Tags (the only accepted vocabulary)
Types (each mod should ideally have at least one): `parts`, `physics`, `plugin`, `app`, `config`,
`library`, `flags`, `agency`, `suits`.
Descriptors (zero or more): `control`, `convenience`, `information`, `editor`, `planet-pack`,
`graphics`, `sound`, `resources`, `science`, `tech-tree`, `career`, `combat`, `comms`, `buildings`,
`crewed`, `uncrewed`, `stock-inventory`, `first-person`.
Guidance: tags are groups useful for filtering, not descriptions. Do not invent tags. `config`
is for mods that add alternative/default configuration (patches, tech trees); a parts mod that
merely ships cfgs is `parts`, not `config`. `library` is for mods that do nothing by themselves.
`plugin` means it ships a DLL. Gameplay descriptors should reflect what the mod changes for the
player (a Kopernicus planet pack -> `planet-pack`; a contract pack -> `career`; IVAs -> `crewed`,
`first-person`; a visual pack -> `graphics`; an autopilot -> `control`; a HUD -> `information`).

## Labels (for communicating with other wranglers)
PR labels: `Fix install`, `Fix license`, `Fix relationships`. Issue labels: `Mod-request`,
`Mod-enhancement`, `Support`. Blocking labels: `Blocked-on-mod-author`, `Blocked-on-dependency`
(an unindexed dependency), `Blocked-on-CKAN-feature` (e.g. wants to overwrite files),
`Blocked-on-other` (unsupported host), `Discussion needed`, `In progress`, `Needs looking into`,
`Easy`, `Critical`.

## Things the wiki calls out as design constraints
- CKAN never overwrites files and has no install order. A mod that must replace another mod's
  files must use ModuleManager patches, or be split into modules with `provides`/`conflicts`
  (Scatterer-config pattern). Metadata cannot fix this; label `Blocked-on-CKAN-feature` or
  `Blocked-on-mod-author`.
- Internal `.ckan` files inside the ZIP can only add properties. If a netkan sets a property
  that the internal `.ckan` also sets, the netkan wins and the internal value is ignored.
- A metanetkan is for authors who want to maintain metadata in their own repo; a single mod is
  usually better served by an internal `.ckan` (keeps metadata versioned with releases).
- ZIPs must extract with ordinary tools; exotic compression methods fail in CKAN
  ("Compression method not supported" on the status page).
