# Uncommon cases and fallbacks

Read the section you need; each is self-contained.

## Contents
- The diagnostic script failed or is incomplete
- CI has not run / cannot run
- The ZIP could not be downloaded or is not a valid ZIP
- Non-Windows machines (mono)
- Forum thread / README cannot be fetched
- Metanetkan PRs (`$kref: '#/ckan/netkan/...'`)
- Internal `.ckan` files inside the ZIP
- Reviving a `.frozen` identifier
- Version ordering problems (epoch, out-of-order, forced `v`)
- Hand-built `download`/`version` or invented `x_netkan` blocks
- Template leftovers (file describes a different mod)
- `.version` file problems
- Several mods or variants in one ZIP
- Craft files, Missions, Scenarios, GameRoot
- Harmony and MiniAVC DLLs
- KSP2 submissions
- Unindexable hosts
- Permission evidence
- Sandbox install failures (`ckan compat add`, unresolvable dependencies)

## The diagnostic script failed or is incomplete
Gather the same facts by hand and continue the checklist:
```bash
gh pr view <N> -R KSP-CKAN/NetKAN --json title,author,body,files,commits,headRefOid,comments,reviews
gh pr diff <N> -R KSP-CKAN/NetKAN
gh api "repos/KSP-CKAN/NetKAN/contents/NetKAN/<Id>.netkan?ref=<headRefOid>" -q .content | base64 -d
gh pr checks <N> -R KSP-CKAN/NetKAN                 # job id is in the link
gh run view --job <JOB_ID> -R KSP-CKAN/NetKAN --log  # grep for '##[error]', '##[warning]', 'Showing'
netkan.exe --game KSP --cachedir <dir> --outputdir <dir> <Id>.netkan   # mono netkan.exe ... on Linux/macOS
unzip -l <cached zip>            # or: python -c "import zipfile,sys;print('\n'.join(zipfile.ZipFile(sys.argv[1]).namelist()))" <zip>
grep -ril '<spacedock id or github repo>' NetKAN/     # duplicate host
ls NetKAN/<Id>.*                                       # existing / frozen
curl -s https://spacedock.info/api/mod/<id>            # license, author, website, versions
curl -s "https://spacedock.info/api/search/mod?query=<name>"
gh api repos/<user>/<repo>/releases?per_page=5
```
netkan.exe: https://ksp-ckan.s3-us-west-2.amazonaws.com/netkan.exe (the script caches it in
`<skill dir>/bin/`; `NETKAN_EXE=<path>` overrides). `--releases 3` inflates older releases when
the ZIP layout may have changed between versions. If PyYAML is not installed the script uses a
built-in mini YAML parser; unusual YAML (anchors, flow mappings across lines) may parse wrongly,
so compare with the raw head content shown in facts.md.

To inspect a release ZIP the script did not analyze (an older release, a second asset):
```bash
curl -sL -o x.zip "<asset url>"     # SpaceDock: https://spacedock.info/mod/<id>/<name>/download/<version>
python -c "import zipfile,sys;print('\n'.join(zipfile.ZipFile(sys.argv[1]).namelist()))" x.zip
python -c "import zipfile,sys;print(zipfile.ZipFile(sys.argv[1]).read(sys.argv[2]).decode('utf-8','replace'))" x.zip "<path in zip>"
```

## CI has not run / cannot run
No check on the PR means the workflow needs a maintainer to click "Approve and run" (first-time
contributors), or the PR was just opened. Rely on local inflation; verdict is at most
`LOOKS CORRECT (CI pending)`. If the check is queued/in progress, say so and use local inflation.
A check that failed for infrastructure reasons (docker pull, cache, GitHub API rate limit) is not
a metadata finding; note it and rely on local inflation.

## The ZIP could not be downloaded or is not a valid ZIP
Say "NOT VERIFIED" for install, bundling, `$vref`, and license-file checks. A download that
fails in CI too ("not a valid ZIP file", "Compression method not supported", HTTP 404/5xx) is a
BLOCKER: the host must serve a plain ZIP (no RAR/7z, no exotic compression, no HTML landing page).
GitHub releases with no asset crash inflation (`assets.First()`): either add
`x_netkan_github: {use_source_archive: true}` (only if the repo root IS the mod layout) or drop the
GitHub document.

## Non-Windows machines (mono)
`netkan.exe` is a .NET Framework binary: run it with `mono netkan.exe ...` (install mono first).
Without mono the script skips local inflation and uses the CI-inflated `.ckan`; if CI has not
run either, ZIP inspection falls back to the host download URLs (SpaceDock latest version,
GitHub latest release asset).

## Forum thread / README cannot be fetched
The KSP forum returns 403 to plain HTTP clients (curl, WebFetch); only the Chrome tools read it
(SKILL.md Step 1 has the exact `javascript_tool` snippet that returns every post). Quirks:
`get_page_text` returns a single post (the newest, or the first unread one), so do not use it;
the topic URL works with any slug as long as the numeric id is right; pages beyond the first are
`<thread URL>page/N/`; `find`/`computer` screenshots work as a slower fallback. If the Chrome
tools are unavailable, use the SpaceDock description (in the bot PR body), the GitHub README
(`gh api repos/<u>/<r>/readme -q .content | base64 -d`), the ZIP's README, and the
`.version`/changelog files, and report anything that needs the thread as "not verified; check the
forum thread".

## Metanetkan PRs (`$kref: '#/ckan/netkan/<url>'`)
The local file is only `identifier` + `$kref` (+ overrides); the remote file is authoritative and
is shown in facts under "Metanetkan". Review the REMOTE content with the normal checklist (the
outer file skips license validation). Extra checks: the remote must not itself be a metanetkan;
the URL should be a raw file on a stable branch; the remote's `identifier` must equal the local
one. Reviewers usually steer single-mod authors toward an internal `.ckan` in the ZIP instead of a
metanetkan, because the metadata then stays versioned with each release; suggest that as a
judgement call, not a correction.

## Internal `.ckan` files inside the ZIP
The file is merged into that release's metadata and can only ADD properties. If the netkan also
sets `depends`/`recommends`/`$vref`, the netkan wins and the internal values are ignored, so
remove them from the netkan when the internal file is meant to carry them. The internal file must
be inside a folder that is actually installed, and its `identifier` must match. When one ZIP
carries several modules with internal `.ckan`s, each netkan needs an explicit `install` stanza so
the right file attaches to the right module. Two `.ckan` files in one ZIP is an error.

## Reviving a `.frozen` identifier
If `NetKAN/<Id>.frozen` exists for the same mod (same SpaceDock id, repo, or folder), the new PR
must reuse that identifier: delete the `.frozen` (CI errors while it exists), modernise the file
(YAML, `$kref`, `$vref`, tags, install, relationships), and keep the identifier so users with the
old install are recognised. Do not add a second identifier for the same mod.

## Version ordering problems (epoch, out-of-order, forced `v`)
- A new release whose version sorts below the previously indexed one triggers automatic epoch
  bumping; `x_netkan_epoch: N` sets a floor explicitly. For a brand-new mod this only matters if
  an older CKAN-meta entry exists (status page / `.frozen`).
- Mods that intentionally publish backports: `x_netkan_allow_out_of_order: true`.
- A mod already indexed WITH a `v` prefix must keep it (`x_netkan_force_v: true` on every host
  document) rather than switching, because `v1.2` sorts above `1.3`.
- SpaceDock versions with spaces, dates, or words (`1.0 beta`, `2024.05.01`) need
  `x_netkan_version_edit` in the SpaceDock document too, and the same regex on every host.

## Hand-built `download`/`version` or invented `x_netkan` blocks
A netkan with `download:`/`version:` and no `$kref`, or with a made-up structure such as
`x_netkan: {github: {repository: ...}}`, pins one release forever and never updates. Replace with
the proper `$kref` (`#/ckan/github/<user>/<repo>` or `#/ckan/spacedock/<id>`). `$kref` plus
`download` in the same document is a CI error.

## Template leftovers (file describes a different mod)
Authors sometimes paste a netkan from their other mod. Compare the `$kref` target (SpaceDock name,
GitHub repo) with the identifier, `name`, tags, depends, and install stanza, and with the ZIP
contents; a mismatch means the whole file must be redone for THIS mod.

## `.version` file problems
- Invalid JSON, or `VERSION`/`KSP_VERSION*` not `{MAJOR, MINOR, PATCH}` objects or strings ->
  `$vref` fails silently; ask the author to fix the file (AVC validator:
  https://github.com/DasSkelett/AVC-VersionFileValidator) and drop `$vref` until then.
- Several `.version` files under the install root -> "Too many .version files": use
  `$vref: '#/ckan/ksp-avc/<path>/<file>.version'`.
- The only `.version` belongs to a bundled third-party mod -> do not set `$vref`.
- `KSP_VERSION` for KSP 2.x or `swinfo.json` present -> wrong repo (see KSP2).
- `.version` `URL` pointing at a branch that no longer exists -> `remote-avc` breaks; mention it.

## Several mods or variants in one ZIP
Two independent mods, mutually exclusive variants (2D/3D, 8k/16k, Stock/RSS configs), or a core
plus optional packs become separate netkans: one per module, each with its own identifier,
`install` (`find` on its folder, `filter` on the others), and `depends` on the core. Wire mutually
exclusive variants with `conflicts` (and `provides` a common virtual name when other mods should
be able to depend on "any variant"). The same download URL may appear in several netkans.

## Craft files, Missions, Scenarios, GameRoot
`.craft` files go to `Ships/VAB` or `Ships/SPH` (`file:` or `find:` per folder, not one stanza per
craft), subassemblies to `Ships/@thumbs`-adjacent folders only if the mod ships them; `Missions`
and `Scenarios` have their own `install_to`; `GameRoot` needs a strong reason and cannot target
`KSP_Data` vs `KSP_x64_Data` conditionally (known spec limitation: `Blocked-on-CKAN-feature`).
Craft files inside GameData trigger a CI warning; either move them to `Ships/...` stanzas or
`filter_regexp: \.craft$` if they are samples.

## Harmony and MiniAVC DLLs
A bundled `0Harmony.dll` without `provides: [Harmony1]` is a CI error; the preferred fix is
`depends: Harmony2` and a `filter` for the bundled DLL. `MiniAVC.dll` inside the mod's own folder
is ignored by the validator; a `MiniAVC` folder at GameData level should be filtered out.

## KSP2 submissions
`swinfo.json`, `BepInEx/plugins`, SpaceDock game id other than 3102, or `.version` with
`KSP_VERSION` 2.x mean the mod belongs in `KSP-CKAN/KSP2-NetKAN`. BLOCKED.

## Unindexable hosts
Supported `$kref` hosts: SpaceDock, GitHub, GitLab (source archives only), Gitea/Forgejo,
SourceForge, Jenkins, plain HTTP with a `.version` file, remote `.version` (`ksp-avc`), metanetkan.
Google Drive, Dropbox, MEGA, Discord/forum attachments, Nexus, CurseForge (API retired), and
pay-walled downloads cannot be indexed: BLOCKED (`Blocked-on-other`), ask the author to publish
on SpaceDock or GitHub releases.

## Permission evidence
Bot PRs: the SpaceDock uploader ticked the CKAN box, which counts as consent only if they are the
author/maintainer. Compare SpaceDock `author`/`shared_authors` with the GitHub owner, `.version`
`GITHUB.USERNAME`, README/LICENSE copyright, and the forum thread author. Human PRs by third
parties need the author's approval (forum post, GitHub comment, Discord screenshot), normally
linked in the PR body. If the body has no link, look for it yourself: a forum post by the author
saying the mod is coming to CKAN, thanking the PR author as a collaborator, or a GitHub issue
counts; report it under "Checked and OK" with the quote and ask, as a judgement-call item, for
the link to be added to the PR body. Only when nothing is found is the verdict BLOCKED
(`Blocked-on-mod-author`), and the report should quote the standard request: "CKAN as a matter of
policy only adds mods if the authors agree. Have these authors agreed? If so, please add a link
to where they agreed in the body of this pull request."
Authors on https://github.com/KSP-CKAN/CKAN/blob/master/policy/Opt-out-list.md are never indexed.

## Sandbox install failures (`ckan compat add`, unresolvable dependencies)
The CI `Installing ...` step installs the module with its `depends` for the newest compatible
game version. Failures: a dependency compatible only with older game versions (add
`ckan compat add 1.10 1.11 1.12` to the PR body to simulate user settings), a dependency that
does not exist (fix the identifier), a `conflicts` with something pulled in by `recommends`
(soften to `suggests`), or two installed modules writing the same file (bundled dependency, or a
module split needed). `ckan install A B` in the PR body adds extra install tests.
