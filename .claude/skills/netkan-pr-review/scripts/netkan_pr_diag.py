#!/usr/bin/env python3
"""
netkan_pr_diag.py - gather every fact needed to review a KSP-CKAN/NetKAN pull request.

This script is DIAGNOSTIC ONLY. It never modifies the repository or the PR.

    python netkan_pr_diag.py <PR_NUMBER> [--repo OWNER/NAME] [--out DIR]
                             [--no-inflate] [--no-ci-log] [--releases N]

What it collects (each section is written to <out>/facts.md and <out>/facts.json):
  1. PR metadata: title, author, body, labels, commits, comments, reviews, changed files
  2. Head/base content of every changed NetKAN/*.netkan|*.frozen|*.ckan file
  3. CI ("Inflate" check) status, and the log's warnings/errors, inflated .ckan, and
     the "Showing N installed files" listing from the sandbox install
  4. Local inflation with netkan.exe (downloaded on demand) for each head netkan
  5. Analysis of the actual download ZIP(s): GameData layout, DLLs, .version files,
     internal .ckan, ModuleManager syntax, craft files, bundled third-party mods,
     license files, junk files, and an approximation of what CKAN would install
  6. Cross-checks against the local NetKAN checkout: identifier collisions, frozen
     files, duplicate $kref, relationship targets that don't exist, other mods that
     already reference this identifier, similar existing identifiers
  7. Upstream host data: SpaceDock API, GitHub API (repo license, releases, assets,
     tags), metanetkan contents, and the CKAN status page entry (if already indexed)

Requires: python3, gh (authenticated), git. netkan.exe is fetched automatically.
"""
import argparse
import base64
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

NETKAN_EXE_URL = "https://ksp-ckan.s3-us-west-2.amazonaws.com/netkan.exe"
STATUS_URL = "https://status.ksp-ckan.space/status/netkan.json"
META_EXT = (".netkan", ".frozen", ".ckan")
DLC_IDS = {"MakingHistory-DLC", "BreakingGround-DLC"}
KNOWN_GAMEDATA_ROOT_DLLS = {"modulemanager": "ModuleManager"}
MM_SYNTAX = re.compile(r"^\s*[@+$\-!%]|^\s*[a-zA-Z0-9_]+:", re.MULTILINE)
CFG_ASPECTS = [
    (re.compile(r"^\s*PART\b", re.M), {"parts"}, []),
    (re.compile(r"^\s*INTERNAL\b", re.M), {"crewed", "first-person"}, []),
    (re.compile(r"^\s*PROP\b", re.M), {"first-person"}, []),
    (re.compile(r"^\s*@TechTree\b", re.M), {"tech-tree"}, []),
    (re.compile(r"^\s*@Kopernicus\b", re.M), {"planet-pack"}, ["Kopernicus"]),
    (re.compile(r"^\s*STATIC\b", re.M), {"buildings"}, ["KerbalKonstructs"]),
    (re.compile(r"^\s*TUFX_PROFILE\b", re.M), {"graphics"}, ["TUFX"]),
    (re.compile(r"^\s*CONTRACT_TYPE\b", re.M), {"career"}, ["ContractConfigurator"]),
    (re.compile(r"^\s*@CUSTOMBARNKIT\b", re.M), set(), ["CustomBarnKit"]),
    (re.compile(r"^\s*name\s*=\s*ModuleB9PartSwitch\b", re.M), set(), ["B9PartSwitch"]),
    (re.compile(r"^\s*name\s*=\s*ModuleWaterfallFX\b", re.M), {"graphics"}, ["Waterfall"]),
    (re.compile(r"^\s*VertexMitchellNetravaliHeightMap\b", re.M), set(), ["VertexMitchellNetravaliHeightMap"]),
    (re.compile(r"^\s*@?PARTUPGRADE\b", re.M), set(), []),
    (re.compile(r"^\s*AGENT\b", re.M), {"agency"}, []),
    (re.compile(r"^\s*EXPERIMENT_DEFINITION\b", re.M), {"science"}, []),
    (re.compile(r"^\s*@?RESOURCE_DEFINITION\b", re.M), {"resources"}, []),
    (re.compile(r"^\s*name\s*=\s*ModuleScatterer|^\s*Scatterer_", re.M), set(), ["Scatterer"]),
    (re.compile(r"^\s*EVE_|^\s*@EVE_", re.M), set(), ["EnvironmentalVisualEnhancements"]),
    (re.compile(r"^\s*KERBALCHANGELOG\b", re.M), set(), ["suggests:KerbalChangelog"]),
    (re.compile(r"^\s*@?PARALLAX\b|ParallaxScatters|Parallax_", re.M), set(), ["Parallax"]),
    (re.compile(r"^\s*name\s*=\s*ModuleRestockDepthMask|Restock", re.M), set(), ["ReStock"]),
]
FILENAME_ASPECTS = [
    (re.compile(r"\.ks$", re.I), {"config", "control"}, ["kOS"]),
    (re.compile(r"\.dll$", re.I), {"plugin"}, []),
    (re.compile(r"\.cfg$", re.I), {"config"}, []),
    (re.compile(r"\.patch$", re.I), {"config"}, ["PatchManager"]),
    (re.compile(r"/(Spaces|Props)/", re.I), {"first-person"}, []),
    (re.compile(r"/Flags/.*\.(png|dds|jpg)$", re.I), {"flags"}, []),
    (re.compile(r"/Suits?/", re.I), {"suits"}, []),
    (re.compile(r"\.(wav|ogg|mp3)$", re.I), {"sound"}, []),
]
JUNK_PATTERNS = [
    re.compile(r"(^|/)__MACOSX(/|$)"), re.compile(r"(^|/)\.DS_Store$"), re.compile(r"(^|/)Thumbs\.db$", re.I),
    re.compile(r"(^|/)\.git(ignore|attributes|modules)?(/|$)"), re.compile(r"\.(pdb|mdb)$", re.I),
    re.compile(r"~$"), re.compile(r"(^|/)desktop\.ini$", re.I), re.compile(r"\.(psd|blend|xcf|max|fbx)$", re.I),
]


def run(cmd, check=False, input_str=None, cwd=None, timeout=600):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       input=input_str, cwd=cwd, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))} failed: {r.stderr.strip()[:500]}")
    return r


def gh_json(*args):
    r = run(["gh", *args])
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def gh_api(path, method="GET"):
    r = run(["gh", "api", "-X", method, path])
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def content_at(repo, path, ref):
    d = gh_api(f"repos/{repo}/contents/{path}?ref={ref}")
    if not d or "content" not in d:
        return None
    try:
        return base64.b64decode(d["content"]).decode("utf-8", errors="replace")
    except Exception:
        return None


def http_get(url, timeout=60, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "netkan-pr-review/1.0 (+https://github.com/KSP-CKAN/NetKAN)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    return data if binary else data.decode("utf-8", errors="replace")


def try_http_get(url, **kw):
    try:
        return http_get(url, **kw)
    except Exception as e:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- parsing helpers

def parse_yaml_or_json_docs(text):
    """Parse a netkan file (YAML multi-doc or JSON, possibly concatenated JSON objects).
    Falls back to a tiny YAML subset parser if PyYAML is unavailable."""
    text = text.lstrip("﻿")
    stripped = text.strip()
    docs = []
    if stripped.startswith("{"):
        dec = json.JSONDecoder()
        idx = 0
        while idx < len(stripped):
            while idx < len(stripped) and stripped[idx] in " \r\n\t":
                idx += 1
            if idx >= len(stripped):
                break
            obj, end = dec.raw_decode(stripped, idx)
            docs.append(obj)
            idx = end
        return docs, "json"
    try:
        import yaml  # type: ignore
        for d in yaml.safe_load_all(text):
            if d is not None:
                docs.append(d)
        return docs, "yaml"
    except ImportError:
        return [mini_yaml(chunk) for chunk in re.split(r"^---\s*$", text, flags=re.M) if chunk.strip()], "yaml(mini)"
    except Exception as e:  # noqa: BLE001
        return [{"_parse_error": str(e)}], "yaml"


def mini_yaml(text):
    """Very small YAML subset parser sufficient for typical netkans (maps, lists, scalars)."""
    lines = [l.rstrip("\n") for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]

    def scalar(v):
        v = v.strip()
        if v.startswith(("'", '"')) and v.endswith(v[0]) and len(v) >= 2:
            return v[1:-1]
        if v in ("true", "True"):
            return True
        if v in ("false", "False"):
            return False
        if re.fullmatch(r"-?\d+", v):
            return int(v)
        if v.startswith("[") and v.endswith("]"):
            return [scalar(x) for x in v[1:-1].split(",") if x.strip()]
        if v.startswith("{") and v.endswith("}"):
            out = {}
            for kv in v[1:-1].split(","):
                if ":" in kv:
                    k, vv = kv.split(":", 1)
                    out[k.strip()] = scalar(vv)
            return out
        return v

    def indent(l):
        return len(l) - len(l.lstrip(" "))

    def parse_block(i, ind):
        # decide list or map
        if i >= len(lines):
            return None, i
        if lines[i].lstrip().startswith("- "):
            out = []
            while i < len(lines) and indent(lines[i]) == ind and lines[i].lstrip().startswith("- "):
                item = lines[i].lstrip()[2:]
                if ":" in item and not item.strip().startswith(("'", '"')):
                    # inline map start inside list item
                    sub_ind = ind + 2
                    lines[i] = " " * sub_ind + item
                    val, i = parse_block(i, sub_ind)
                    out.append(val)
                else:
                    out.append(scalar(item))
                    i += 1
            return out, i
        out = {}
        while i < len(lines) and indent(lines[i]) == ind:
            l = lines[i].strip()
            if l.startswith("- "):
                break
            if ":" not in l:
                i += 1
                continue
            k, v = l.split(":", 1)
            k = k.strip().strip("'\"")
            v = v.strip()
            if v in ("", "|", ">", "|-", ">-"):
                if i + 1 < len(lines) and indent(lines[i + 1]) > ind:
                    if v in ("|", ">", "|-", ">-"):
                        j = i + 1
                        buf = []
                        while j < len(lines) and indent(lines[j]) > ind:
                            buf.append(lines[j].strip())
                            j += 1
                        out[k] = (" " if v.startswith(">") else "\n").join(buf)
                        i = j
                    else:
                        val, i = parse_block(i + 1, indent(lines[i + 1]))
                        out[k] = val
                else:
                    out[k] = None
                    i += 1
            else:
                out[k] = scalar(v)
                i += 1
        return out, i

    val, _ = parse_block(0, indent(lines[0]) if lines else 0)
    return val if isinstance(val, dict) else {"_doc": val}


def rel_names(doc, key):
    out = []
    for r in doc.get(key) or []:
        if isinstance(r, dict):
            if "any_of" in r:
                out.extend(x.get("name") for x in r["any_of"] if isinstance(x, dict))
            elif "name" in r:
                out.append(r["name"])
        elif isinstance(r, str):
            out.append(r)
    return [x for x in out if x]


# --------------------------------------------------------------------------- repo cross-checks

def find_repo_root(start):
    p = Path(start).resolve()
    for cand in [p, *p.parents]:
        if (cand / "NetKAN").is_dir() and (cand / ".git").exists():
            return cand
    r = run(["git", "rev-parse", "--show-toplevel"], cwd=str(p))
    if r.returncode == 0:
        root = Path(r.stdout.strip())
        if (root / "NetKAN").is_dir():
            return root
    return None


def load_local_index(root):
    """Index of every netkan/frozen on the local checkout: identifier -> info."""
    idx = {}
    krefs = {}
    provides = {}
    references = {}
    for f in sorted((root / "NetKAN").iterdir()):
        if f.suffix not in (".netkan", ".frozen"):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        ident = f.stem
        info = {"file": f.name, "frozen": f.suffix == ".frozen"}
        idx[ident] = info
        for m in re.finditer(r"#/ckan/(spacedock|github|gitlab|gitea|sourceforge|jenkins|http|netkan|ksp-avc)/([^'\"\s]+)", text):
            key = (m.group(1), m.group(2).rstrip("/").lower())
            if m.group(1) == "github":
                key = ("github", "/".join(m.group(2).split("/")[:2]).lower())
            krefs.setdefault(key, []).append(ident)
        for m in re.finditer(r"provides\"?\s*:\s*\[([^\]]*)\]", text):
            for p in re.findall(r"\"([^\"]+)\"", m.group(1)):
                provides.setdefault(p, []).append(ident)
        for m in re.finditer(r"provides:\s*\n((?:\s*-\s*[^\n]+\n?)+)", text):
            for p in re.findall(r"-\s*([^\n#]+)", m.group(1)):
                provides.setdefault(p.strip().strip("'\""), []).append(ident)
        for m in re.finditer(r"name\"?\s*:\s*\"?'?([A-Za-z0-9][A-Za-z0-9-]*)", text):
            references.setdefault(m.group(1), set()).add(ident)
    return idx, krefs, provides, references


# --------------------------------------------------------------------------- CI

def ci_info(repo, pr, want_log):
    checks = gh_json("pr", "checks", str(pr), "-R", repo, "--json", "name,state,link,workflow,bucket,startedAt,completedAt") or []
    out = {"checks": checks, "inflate": None}
    inflate = next((c for c in checks if c.get("name") == "Inflate" or c.get("workflow") == "Inflate netkans"), None)
    if not inflate:
        return out
    m = re.search(r"/actions/runs/(\d+)/job/(\d+)", inflate.get("link") or "")
    info = {"state": inflate.get("state"), "bucket": inflate.get("bucket"), "link": inflate.get("link"),
            "started_at": inflate.get("startedAt"), "completed_at": inflate.get("completedAt")}
    if m:
        info["run_id"], info["job_id"] = m.group(1), m.group(2)
    out["inflate"] = info
    if not want_log or not m:
        return out
    r = run(["gh", "run", "view", "--job", m.group(2), "-R", repo, "--log"], timeout=300)
    if r.returncode != 0:
        info["log_error"] = r.stderr.strip()[:300]
        return out
    lines = []
    for raw in r.stdout.splitlines():
        parts = raw.split("\t", 2)
        line = parts[2] if len(parts) == 3 else raw
        line = re.sub(r"^﻿?[0-9T:.\-]+Z ", "", line)
        lines.append(line)
    info["log_lines"] = len(lines)
    info["log"] = "\n".join(lines)
    ann = [l for l in lines if l.startswith(("##[warning]", "##[error]", "::warning", "::error", "::notice"))]
    # netkan.exe validates once per host document/download, so a two-host netkan prints the same
    # warning twice; collapse duplicates so they read as ONE finding
    counts = {}
    for l in ann:
        key = re.sub(r"^(##\[\w+\]|::\w+::)\d+ \[\d+\] ", r"\1", l)  # drop log4net elapsed-ms + thread id
        counts[key] = counts.get(key, 0) + 1
    info["annotations_raw"] = ann
    info["annotations"] = [f"{l}   <- same message x{c} (one per host document): ONE finding" if c > 1 else l
                           for l, c in counts.items()]
    # groups
    groups = {}
    cur = None
    for l in lines:
        if l.startswith("##[group]"):
            cur = l[len("##[group]"):]
            groups[cur] = []
        elif l.startswith("##[endgroup]"):
            cur = None
        elif cur is not None:
            groups[cur].append(l)
    info["groups"] = {k: v for k, v in groups.items() if k.startswith(("Inflating", "Installing", "Diffing", "Validating", "Run KSP-CKAN"))}
    installed = {}
    for k, v in groups.items():
        if k.startswith("Installing"):
            txt = "\n".join(v)
            mm = re.search(r"Showing (\d+) installed files:\n((?:\s+- .*\n?)+)", txt)
            if mm:
                installed[k] = [x.strip()[2:] for x in mm.group(2).strip().splitlines()]
    info["installed_files"] = installed
    ckans = {}
    for k, v in groups.items():
        if k.startswith("Inflating"):
            txt = "\n".join(v)
            for mm in re.finditer(r"^(\S+\.ckan):\n(\{.*?^\})", txt, re.S | re.M):
                try:
                    ckans[mm.group(1)] = json.loads(mm.group(2))
                except json.JSONDecodeError:
                    ckans[mm.group(1)] = mm.group(2)
    info["inflated_ckans"] = ckans
    return out


# --------------------------------------------------------------------------- local inflation

def ensure_netkan_exe(bin_dir):
    env = os.environ.get("NETKAN_EXE")
    if env and Path(env).exists():
        return Path(env)
    exe = bin_dir / "netkan.exe"
    if exe.exists():
        return exe
    bin_dir.mkdir(parents=True, exist_ok=True)
    print(f"[diag] downloading netkan.exe from {NETKAN_EXE_URL} -> {exe}", file=sys.stderr)
    try:
        data = http_get(NETKAN_EXE_URL, timeout=300, binary=True)
        exe.write_bytes(data)
        return exe
    except Exception as e:  # noqa: BLE001
        print(f"[diag] could not download netkan.exe: {e}", file=sys.stderr)
        return None


def netkan_cmd(exe):
    if os.name == "nt":
        return [str(exe)]
    mono = shutil.which("mono")
    return [mono, str(exe)] if mono else None


def inflate_local(exe, netkan_path, outdir, cachedir, releases, game="KSP"):
    cmd = netkan_cmd(exe)
    if not cmd:
        return {"error": "mono not found; cannot run netkan.exe on this platform"}
    outdir.mkdir(parents=True, exist_ok=True)
    cachedir.mkdir(parents=True, exist_ok=True)
    args = [*cmd, "--game", game, "--cachedir", str(cachedir), "--outputdir", str(outdir), "--releases", str(releases)]
    tok = run(["gh", "auth", "token"])
    if tok.returncode == 0 and tok.stdout.strip():
        args += ["--github-token", tok.stdout.strip()]
    args.append(str(netkan_path))
    r = run(args, timeout=900)
    log = (r.stdout + "\n" + r.stderr).strip()
    log = re.sub(r"--github-token \S+", "--github-token ***", log)
    ckans = {}
    for f in sorted(outdir.glob("*.ckan")):
        try:
            ckans[f.name] = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            ckans[f.name] = {"_error": str(e)}
    return {
        "exit_code": r.returncode,
        "log": log,
        "messages": [l for l in log.splitlines() if re.search(r"\b(WARN|ERROR|FATAL)\b", l)],
        "ckans": ckans,
    }


# --------------------------------------------------------------------------- zip analysis

def find_cached_zip(cachedir, ckan):
    h = ckan.get("download_hash") or {}
    sha1 = (h.get("sha1") or "").lower()
    sha256 = (h.get("sha256") or "").lower()
    for z in cachedir.glob("*.zip"):
        try:
            s1 = z.with_suffix(z.suffix + ".sha1")
            if sha1 and s1.exists() and s1.read_text().strip().lower() == sha1:
                return z
            data = z.read_bytes()
            if sha1 and hashlib.sha1(data).hexdigest() == sha1:
                return z
            if sha256 and hashlib.sha256(data).hexdigest() == sha256:
                return z
        except Exception:
            continue
    return None


def download_zip(url, cachedir):
    cachedir.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha1(url.encode()).hexdigest()[:8] + "-" + re.sub(r"[^A-Za-z0-9._-]+", "_", url.rsplit("/", 1)[-1])[:60]
    if not name.lower().endswith(".zip"):
        name += ".zip"
    dest = cachedir / name
    if dest.exists():
        return dest
    data = http_get(url, timeout=600, binary=True)
    dest.write_bytes(data)
    return dest


def apply_install_stanzas(names, ckan, identifier):
    """Approximate CKAN's install logic to list destination paths. Returns (dest_list, notes)."""
    stanzas = ckan.get("install") or [{"find": identifier, "install_to": "GameData"}]
    dests = []
    notes = []
    dirs = set()
    for n in names:
        parts = n.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))
    for st in stanzas:
        install_to = st.get("install_to", "GameData")
        matched_root = None
        if "file" in st:
            matched_root = st["file"].rstrip("/")
        elif "find" in st:
            want = st["find"].rstrip("/")
            cands = sorted([d for d in dirs if d.split("/")[-1] == want or d == want], key=lambda d: d.count("/"))
            if not cands and st.get("find_matches_files"):
                cands = sorted([f for f in names if f.split("/")[-1] == want], key=lambda d: d.count("/"))
            matched_root = cands[0] if cands else None
        elif "find_regexp" in st:
            rx = re.compile(st["find_regexp"])
            cands = sorted([d for d in dirs if rx.search(d)], key=lambda d: d.count("/"))
            if not cands and st.get("find_matches_files"):
                cands = sorted([f for f in names if rx.search(f)], key=lambda d: d.count("/"))
            matched_root = cands[0] if cands else None
        if matched_root is None:
            notes.append(f"stanza {json.dumps(st)} matched nothing")
            continue
        filters = st.get("filter") or []
        filters = [filters] if isinstance(filters, str) else filters
        filter_rx = st.get("filter_regexp") or []
        filter_rx = [filter_rx] if isinstance(filter_rx, str) else filter_rx
        inc = st.get("include_only") or []
        inc = [inc] if isinstance(inc, str) else inc
        inc_rx = st.get("include_only_regexp") or []
        inc_rx = [inc_rx] if isinstance(inc_rx, str) else inc_rx
        as_name = st.get("as")
        root_leaf = matched_root.split("/")[-1]
        count = 0
        for n in names:
            if n == matched_root or n.startswith(matched_root + "/"):
                rel = n[len(matched_root):].lstrip("/")
                parts = ("/".join([root_leaf, rel]) if rel else root_leaf).split("/")
                if any(p.lower() in [f.lower() for f in filters] for p in parts):
                    continue
                if any(re.search(rx, n) for rx in filter_rx):
                    continue
                if inc and not any(p.lower() in [x.lower() for x in inc] for p in parts):
                    continue
                if inc_rx and not any(re.search(rx, n) for rx in inc_rx):
                    continue
                leaf = as_name or root_leaf
                dest = f"{install_to}/{leaf}" + (f"/{rel}" if rel else "")
                dests.append(dest)
                count += 1
        notes.append(f"stanza {json.dumps(st)} -> matched '{matched_root}', {count} files")
    return dests, notes


def analyze_zip(zpath, ckan, identifier, local_index):
    res = {"zip": str(zpath), "size": zpath.stat().st_size}
    try:
        zf = zipfile.ZipFile(zpath)
    except zipfile.BadZipFile as e:
        res["error"] = f"not a valid zip: {e}"
        return res
    infos = [i for i in zf.infolist() if not i.is_dir()]
    names = [i.filename.replace("\\", "/") for i in infos]
    res["file_count"] = len(names)
    res["files"] = names
    res["top_level"] = sorted({n.split("/")[0] for n in names})
    gd_dirs = set()
    gd_root_files = set()
    nested_gd = set()
    for n in names:
        parts = n.split("/")
        lower = [p.lower() for p in parts]
        if "gamedata" in lower:
            i = lower.index("gamedata")
            if "gamedata" in lower[i + 1:]:
                nested_gd.add(n)
            if i + 1 < len(parts) - 1:
                gd_dirs.add("/".join(parts[: i + 2]))
            elif i + 1 == len(parts) - 1:
                gd_root_files.add(n)
    res["gamedata_dirs"] = sorted(gd_dirs)
    res["gamedata_root_files"] = sorted(gd_root_files)
    res["nested_gamedata"] = sorted(nested_gd)
    res["has_gamedata"] = bool(gd_dirs or gd_root_files)
    all_dirs = set()
    for n in names:
        parts = n.split("/")
        for i in range(1, len(parts)):
            all_dirs.add("/".join(parts[:i]))
    res["identifier_dir_exact"] = sorted(d for d in all_dirs if d.split("/")[-1] == identifier)
    res["identifier_dir_ci"] = sorted(d for d in all_dirs if d.split("/")[-1].lower() == identifier.lower() and d.split("/")[-1] != identifier)
    dlls = [n for n in names if n.lower().endswith(".dll")]
    res["dlls"] = dlls
    dll_idents = sorted({Path(d).stem for d in dlls})
    res["dll_identifiers"] = dll_idents
    res["dll_matches_identifier"] = identifier in dll_idents
    res["source_code"] = [n for n in names if n.lower().endswith((".cs", ".csproj", ".sln"))][:50]
    # version files
    vfiles = []
    for n in names:
        if n.lower().endswith(".version"):
            raw = ""
            parsed = None
            try:
                raw = zf.read(n).decode("utf-8-sig", errors="replace")
                if raw.strip().startswith("{"):
                    try:
                        parsed = json.loads(raw, strict=False)
                    except json.JSONDecodeError:
                        parsed = json.loads(re.sub(r"^\s*//.*$", "", raw, flags=re.M), strict=False)
            except Exception as e:  # noqa: BLE001
                parsed = {"_error": str(e), "_raw_head": raw[:800]}
            vfiles.append({"path": n, "content": parsed if parsed is not None else raw[:1500]})
    res["version_files"] = vfiles
    res["swinfo"] = [n for n in names if n.lower().endswith("swinfo.json")]
    # internal ckan
    ick = []
    for n in names:
        if n.lower().endswith(".ckan"):
            try:
                ick.append({"path": n, "content": zf.read(n).decode("utf-8-sig", errors="replace")[:4000]})
            except Exception as e:  # noqa: BLE001
                ick.append({"path": n, "error": str(e)})
    res["internal_ckan"] = ick
    # cfg analysis
    cfgs = [n for n in names if n.lower().endswith(".cfg")]
    res["cfg_count"] = len(cfgs)
    mm_files, tags, deps = [], set(), []
    aspect_hits = {}
    for n in cfgs:
        try:
            txt = zf.read(n).decode("utf-8-sig", errors="ignore")
        except Exception:
            continue
        if MM_SYNTAX.search(txt):
            mm_files.append(n)
        for rx, t, d in CFG_ASPECTS:
            if rx.search(txt):
                tags |= t
                for dd in d:
                    if dd not in deps:
                        deps.append(dd)
                aspect_hits.setdefault(rx.pattern, []).append(n)
    for n in names:
        for rx, t, d in FILENAME_ASPECTS:
            if rx.search(n):
                tags |= t
                for dd in d:
                    if dd not in deps:
                        deps.append(dd)
    if "parts" in tags and "config" in tags:
        tags.discard("config")
    if mm_files and "ModuleManager" not in deps:
        deps.insert(0, "ModuleManager")
    res["modulemanager_syntax_files"] = mm_files[:40]
    res["modulemanager_syntax_count"] = len(mm_files)
    res["suggested_tags"] = sorted(tags)
    res["suggested_depends"] = [d for d in deps if not d.startswith("suggests:")]
    res["suggested_suggests"] = [d.split(":", 1)[1] for d in deps if d.startswith("suggests:")]
    # .version sanity (KSP-AVC): NAME should be the mod, VERSION/KSP_VERSION* objects or strings
    avc_notes = []
    for v in vfiles:
        c = v["content"]
        if not isinstance(c, dict) or "_error" in c:
            avc_notes.append(f"{v['path']}: not valid JSON ({(c or {}).get('_error') if isinstance(c, dict) else 'text'}); $vref would fail")
            continue
        for key in ("VERSION", "KSP_VERSION", "KSP_VERSION_MIN", "KSP_VERSION_MAX"):
            if key in c and not isinstance(c[key], (dict, str)):
                avc_notes.append(f"{v['path']}: {key} is {type(c[key]).__name__}, expected object {{MAJOR,MINOR,PATCH}} or string")
        if "VERSION" not in c:
            avc_notes.append(f"{v['path']}: no VERSION field")
        if not any(k in c for k in ("KSP_VERSION", "KSP_VERSION_MIN", "KSP_VERSION_MAX")):
            avc_notes.append(f"{v['path']}: no KSP_VERSION/MIN/MAX (no compatibility info; $vref adds nothing)")
        nm = str(c.get("NAME", ""))
        if nm and re.sub(r"[\W_]+", "", nm).lower() != identifier.lower() and nm.lower() != identifier.lower():
            avc_notes.append(f"{v['path']}: NAME '{nm}' differs from identifier '{identifier}' (fine if it is just the display name; suspicious if it names ANOTHER mod, i.e. a bundled dependency's .version)")
        if not v["path"].lower().split("/")[-1].startswith(identifier.lower()[:6]):
            avc_notes.append(f"{v['path']}: filename does not resemble identifier; check it is this mod's own .version and not a bundled mod's")
    res["version_file_notes"] = avc_notes
    res["find_targets_other_mod"] = []
    res["aspect_hits"] = {k: v[:5] for k, v in aspect_hits.items()}
    # crafts
    crafts = []
    for n in names:
        if n.lower().endswith(".craft"):
            try:
                txt = zf.read(n).decode("utf-8-sig", errors="ignore")
                m = re.search(r"^\s*type = (VAB|SPH|None)", txt, re.M)
                crafts.append({"path": n, "type": m.group(1) if m else "?"})
            except Exception:
                crafts.append({"path": n, "type": "?"})
    res["crafts"] = crafts
    res["ks_scripts"] = [n for n in names if n.lower().endswith(".ks")]
    res["patch_files"] = [n for n in names if n.lower().endswith(".patch")]
    # license / readme
    lic = []
    for n in names:
        base = n.split("/")[-1].lower()
        if base.startswith(("license", "licence", "copying")) or base in ("unlicense", "unlicense.txt"):
            try:
                head = zf.read(n).decode("utf-8-sig", errors="replace")
                lic.append({"path": n, "head": head[:700], "guess": guess_license(head)})
            except Exception:
                lic.append({"path": n})
    res["license_files"] = lic
    readmes = []
    for n in names:
        base = n.split("/")[-1].lower()
        if base.startswith("readme"):
            try:
                readmes.append({"path": n, "head": zf.read(n).decode("utf-8-sig", errors="replace")[:1200]})
            except Exception:
                pass
    res["readmes"] = readmes[:3]
    res["junk_files"] = [n for n in names if any(rx.search(n) for rx in JUNK_PATTERNS)][:40]
    # bundled third-party mods: dirs directly under GameData (or top-level dirs if no GameData) that
    # match another identifier in the local NetKAN index, plus ModuleManager dlls
    bundled = []
    cand_dirs = [d.split("/")[-1] for d in gd_dirs] if gd_dirs else [d for d in res["top_level"] if "." not in d]
    lower_index = {k.lower(): k for k in local_index}
    for d in sorted(set(cand_dirs)):
        if d == identifier:
            continue
        hit = lower_index.get(d.lower()) or lower_index.get(re.sub(r"^\d+_?", "", d).lower())
        if hit and hit != identifier:
            bundled.append({"folder": d, "looks_like": hit, "frozen": local_index[hit]["frozen"]})
    for n in dlls:
        base = n.split("/")[-1].lower()
        if base.startswith("modulemanager"):
            bundled.append({"folder": n, "looks_like": "ModuleManager", "frozen": False})
        if "harmony" in base and identifier != "Harmony2":
            bundled.append({"folder": n, "looks_like": "Harmony (0Harmony.dll -> Harmony1/Harmony2)", "frozen": False})
        if base.startswith("miniavc"):
            bundled.append({"folder": n, "looks_like": "MiniAVC (bundled version checker; usually filtered or ignored)", "frozen": False})
    res["bundled_candidates"] = bundled
    for st in ckan.get("install") or []:
        tgt = (st.get("find") or st.get("file") or "").rstrip("/").split("/")[-1]
        hit = lower_index.get(tgt.lower()) if tgt else None
        if hit and hit != identifier:
            res["find_targets_other_mod"].append({"stanza": st, "existing_identifier": hit,
                                                  "note": "install stanza targets a folder named like another indexed mod; files will land inside that mod's directory (OK only if they are add-on files like profiles/patches that never collide with the other mod's own files; otherwise use depends + a narrower find)"})
    # approximate install
    dests, notes = apply_install_stanzas(names, ckan, identifier)
    res["approx_install_notes"] = notes
    res["approx_installed_files"] = dests
    res["approx_installed_count"] = len(dests)
    not_installed = [n for n in names if not any(n.endswith("/".join(d.split("/")[1:])) or n.split("/")[-1] == d.split("/")[-1] for d in dests)]
    res["approx_not_installed"] = not_installed[:60]
    res["approx_not_installed_count"] = len(not_installed)
    installed_dlls = [d for d in dests if d.lower().endswith(".dll")]
    res["approx_installed_dlls"] = installed_dlls
    res["approx_installed_gamedata_dirs"] = sorted({"/".join(d.split("/")[:2]) for d in dests if d.startswith("GameData/")})
    return res


def guess_license(text):
    t = text.lower()
    checks = [
        ("GPL-3.0", ["gnu general public license", "version 3"]), ("GPL-2.0", ["gnu general public license", "version 2"]),
        ("LGPL-3.0", ["lesser general public license", "version 3"]), ("LGPL-2.1", ["lesser general public license", "version 2.1"]),
        ("AGPL-3.0", ["affero"]), ("MIT", ["permission is hereby granted, free of charge"]), ("Apache-2.0", ["apache license", "2.0"]),
        ("BSD-3-clause", ["redistribution and use", "neither the name"]), ("BSD-2-clause", ["redistribution and use"]),
        ("MPL-2.0", ["mozilla public license", "2.0"]), ("Unlicense", ["this is free and unencumbered software"]),
        ("WTFPL", ["do what the fuck you want"]), ("CC0", ["cc0", "public domain dedication"]),
        ("CC-BY-NC-ND-4.0", ["attribution-noncommercial-noderivatives 4.0"]), ("CC-BY-NC-SA-4.0", ["attribution-noncommercial-sharealike 4.0"]),
        ("CC-BY-NC-4.0", ["attribution-noncommercial 4.0"]), ("CC-BY-SA-4.0", ["attribution-sharealike 4.0"]), ("CC-BY-4.0", ["attribution 4.0"]),
        ("CC-BY-NC-SA-3.0", ["attribution-noncommercial-sharealike 3.0"]), ("CC-BY-NC-ND-3.0", ["attribution-noncommercial-noderivatives 3.0"]),
        ("CC-BY-SA-3.0", ["attribution-sharealike 3.0"]), ("CC-BY-3.0", ["attribution 3.0"]),
        ("CC-BY-NC-SA", ["cc-by-nc-sa", "by-nc-sa"]), ("CC-BY-NC-ND", ["cc-by-nc-nd", "by-nc-nd"]), ("CC-BY-NC", ["cc-by-nc", "by-nc"]),
        ("CC-BY-SA", ["cc-by-sa", "by-sa"]), ("CC-BY", ["cc-by", "creative commons attribution"]),
        ("restricted (all rights reserved)", ["all rights reserved"]),
    ]
    for name, needles in checks:
        if all(n in t for n in needles):
            return name
    return "unknown"


# --------------------------------------------------------------------------- hosts

def spacedock_info(sd_id):
    txt = try_http_get(f"https://spacedock.info/api/mod/{sd_id}")
    if not txt:
        return {"error": "SpaceDock API unreachable or mod not found"}
    try:
        d = json.loads(txt)
    except json.JSONDecodeError:
        return {"error": "SpaceDock API returned non-JSON"}
    if "error" in d and d.get("error"):
        return {"error": d.get("reason") or d.get("error")}
    return {
        "id": d.get("id"), "name": d.get("name"), "author": d.get("author"),
        "shared_authors": [a.get("username") for a in d.get("shared_authors") or []],
        "license": d.get("license"), "website": d.get("website"), "source_code": d.get("source_code"),
        "game": d.get("game"), "game_id": d.get("game_id"), "ckan": d.get("ckan"),
        "short_description": d.get("short_description"), "url": d.get("url"),
        "versions": [{"friendly_version": v.get("friendly_version"), "game_version": v.get("game_version"),
                      "created": v.get("created"), "download_path": v.get("download_path")} for v in (d.get("versions") or [])[:8]],
        "version_count": len(d.get("versions") or []),
    }


def apply_version_edit(version_edit, s):
    """Apply an x_netkan_version_edit (string or {find, replace}) to s; None if the regex does not match."""
    find = version_edit.get("find") if isinstance(version_edit, dict) else version_edit
    repl = version_edit.get("replace", "${version}") if isinstance(version_edit, dict) else "${version}"
    find = re.sub(r"\(\?<([A-Za-z_][A-Za-z0-9_]*)>", r"(?P<\1>", str(find or ""))  # C# named groups -> Python
    m = re.match(find, str(s))
    if not m:
        return None
    v = repl
    for k, val in m.groupdict().items():
        v = v.replace("${" + k + "}", val or "")
    return v


def github_info(owner, repo, version_edit=None):
    r = gh_api(f"repos/{owner}/{repo}") or {}
    out = {
        "full_name": r.get("full_name"), "license_spdx": (r.get("license") or {}).get("spdx_id"),
        "archived": r.get("archived"), "fork": r.get("fork"), "parent": (r.get("parent") or {}).get("full_name"),
        "default_branch": r.get("default_branch"), "homepage": r.get("homepage"), "description": r.get("description"),
        "pushed_at": r.get("pushed_at"), "owner": (r.get("owner") or {}).get("login"),
    }
    if not r:
        out["error"] = "GitHub repo not found or API error"
        return out
    rels = gh_api(f"repos/{owner}/{repo}/releases?per_page=8") or []
    out["releases"] = [{
        "tag_name": x.get("tag_name"), "name": x.get("name"), "prerelease": x.get("prerelease"), "draft": x.get("draft"),
        "published_at": x.get("published_at"), "assets": [a.get("name") for a in x.get("assets") or []],
        "asset_sizes": [a.get("size") for a in x.get("assets") or []],
    } for x in rels]
    out["release_count_fetched"] = len(rels)
    tags = [t.get("tag_name") for t in rels if t.get("tag_name")]
    out["tag_prefix_variety"] = sorted({re.match(r"^[^0-9]*", t).group(0) for t in tags})
    if version_edit:
        edited = []
        for t in tags:
            try:
                v = apply_version_edit(version_edit, t)
                if v is not None:
                    edited.append({"tag": t, "version": v})
                else:
                    edited.append({"tag": t, "version": None, "note": "version_edit regex does not match (strict=true would fail)"})
            except re.error as e:
                edited.append({"tag": t, "error": str(e)})
        out["version_edit_applied"] = edited
    lic_paths = []
    try:
        tree = gh_api(f"repos/{owner}/{repo}/contents/") or []
        lic_paths = [f.get("name") for f in tree if isinstance(f, dict) and re.match(r"(?i)^(license|licence|copying)", f.get("name") or "")]
        out["root_files"] = [f.get("name") for f in tree if isinstance(f, dict)][:40]
    except Exception:
        pass
    out["license_files_in_repo_root"] = lic_paths
    return out


def spacedock_search(query):
    txt = try_http_get(f"https://spacedock.info/api/search/mod?query={urllib.request.quote(query)}", timeout=60)
    if not txt:
        return None
    try:
        d = json.loads(txt)
    except json.JSONDecodeError:
        return None
    return [{"id": m.get("id"), "name": m.get("name"), "author": m.get("author"), "game_id": m.get("game_id"),
             "url": "https://spacedock.info" + (m.get("url") or "")} for m in d[:12]] if isinstance(d, list) else None


def precedents(root, local_index, dep_names, exclude, limit=4):
    """Existing netkans that depend on the same key mods: shows the house style for install/tags."""
    out = {}
    for dep in dep_names:
        hits = []
        for ident, info in local_index.items():
            if info["frozen"] or ident == exclude:
                continue
            try:
                text = (root / "NetKAN" / info["file"]).read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if re.search(r"name\"?\s*:\s*\"?'?" + re.escape(dep) + r"['\"]?\s*$", text, re.M):
                hits.append((ident, text))
            if len(hits) >= limit * 3:
                break
        # prefer ones with an install stanza (more informative), then short files
        hits.sort(key=lambda h: (("install" not in h[1]), len(h[1])))
        out[dep] = [{"identifier": i, "netkan": t[:1500]} for i, t in hits[:limit]]
    return out


def status_entry(identifier, cache_dir):
    cache = cache_dir / "netkan_status.json"
    try:
        if not cache.exists() or time.time() - cache.stat().st_mtime > 6 * 3600:
            data = http_get(STATUS_URL, timeout=120)
            cache.write_text(data, encoding="utf-8")
        d = json.loads(cache.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"error": f"status page unavailable: {e}"}
    e = d.get(identifier)
    if not e:
        ci = {k.lower(): k for k in d}
        if identifier.lower() in ci:
            return {"case_insensitive_match": ci[identifier.lower()], "entry": d[ci[identifier.lower()]]}
        return None
    return {"entry": e}


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pr", type=int)
    ap.add_argument("--repo", default="KSP-CKAN/NetKAN")
    ap.add_argument("--out", default=None, help="output directory (default: <tmp>/netkan-pr-review/pr-<N>)")
    ap.add_argument("--no-inflate", action="store_true", help="skip local netkan.exe inflation")
    ap.add_argument("--no-ci-log", action="store_true", help="skip downloading the CI job log")
    ap.add_argument("--no-zip", action="store_true", help="skip download/analysis of the mod zip")
    ap.add_argument("--releases", type=int, default=1, help="how many releases to inflate locally")
    ap.add_argument("--netkan-dir", default=None, help="path to local NetKAN checkout (auto-detected)")
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    persist = Path(os.environ.get("NETKAN_REVIEW_HOME") or (Path.home() / ".cache" / "netkan-pr-review"))
    persist.mkdir(parents=True, exist_ok=True)
    cachedir = persist / "downloads"
    cachedir.mkdir(parents=True, exist_ok=True)
    out = Path(args.out) if args.out else Path(tempfile.gettempdir()) / "netkan-pr-review" / f"pr-{args.pr}"
    out.mkdir(parents=True, exist_ok=True)
    facts = {"pr": args.pr, "repo": args.repo, "out_dir": str(out), "sections": {}}
    S = facts["sections"]
    md = []

    def section(title):
        md.append(f"\n## {title}\n")

    def block(text, lang=""):
        md.append(f"```{lang}\n{text.rstrip()}\n```")

    # 1. PR metadata ---------------------------------------------------------
    pr = gh_json("pr", "view", str(args.pr), "-R", args.repo, "--json",
                 "number,title,author,body,state,isDraft,createdAt,updatedAt,mergedAt,labels,files,commits,headRefOid,baseRefOid,headRefName,headRepository,headRepositoryOwner,comments,reviews,mergeable,url")
    if not pr:
        print(f"Could not fetch PR #{args.pr} from {args.repo}; is gh authenticated?", file=sys.stderr)
        sys.exit(2)
    head = pr["headRefOid"]
    base = pr["baseRefOid"]
    files = [f["path"] for f in pr.get("files") or []]
    S["pr"] = {k: pr.get(k) for k in ("number", "title", "state", "isDraft", "createdAt", "updatedAt", "mergedAt", "url", "headRefOid", "baseRefOid", "headRefName", "mergeable")}
    S["pr"]["author"] = pr["author"]["login"]
    S["pr"]["head_repo"] = f"{(pr.get('headRepositoryOwner') or {}).get('login')}/{(pr.get('headRepository') or {}).get('name')}"
    S["pr"]["labels"] = [l["name"] for l in pr.get("labels") or []]
    S["pr"]["files"] = [{"path": f["path"], "additions": f.get("additions"), "deletions": f.get("deletions")} for f in pr.get("files") or []]
    S["pr"]["commits"] = [{"sha": c["oid"][:8], "author": ((c.get("authors") or [{}])[0].get("login") or (c.get("authors") or [{}])[0].get("name")), "message": c["messageHeadline"]} for c in pr.get("commits") or []]
    S["pr"]["body"] = pr.get("body") or ""
    S["pr"]["comments"] = [{"author": c["author"]["login"], "date": c["createdAt"][:10], "body": c["body"]} for c in pr.get("comments") or []]
    S["pr"]["reviews"] = [{"author": r["author"]["login"], "state": r["state"], "date": (r.get("submittedAt") or "")[:10], "body": r.get("body") or ""} for r in pr.get("reviews") or []]
    inline = gh_api(f"repos/{args.repo}/pulls/{args.pr}/comments") or []
    S["pr"]["inline_comments"] = [{"author": c["user"]["login"], "path": c.get("path"), "line": c.get("line") or c.get("original_line"), "body": c.get("body")} for c in inline]
    body = S["pr"]["body"]
    S["pr"]["is_spacedock_bot"] = S["pr"]["author"] == "netkan-bot" or "automatically generated by SpaceDock" in body
    S["pr"]["pr_body_compat_override"] = re.findall(r"ckan compat add((?: [0-9.]+)+)", body)
    S["pr"]["pr_body_install_tests"] = re.findall(r"ckan install((?: [A-Za-z][A-Za-z0-9-]*(?:=\S+)?)+)", body)
    S["pr"]["pr_body_empty"] = len(body.strip()) == 0

    md.append(f"# NetKAN PR #{args.pr} diagnostic facts: {pr['title']}\n")
    md.append(f"- URL: {pr['url']}\n- Author: {S['pr']['author']} (SpaceDock bot PR: {S['pr']['is_spacedock_bot']})\n- State: {pr['state']} draft={pr['isDraft']} mergeable={pr.get('mergeable')}\n- Created: {pr['createdAt'][:10]}  Updated: {pr['updatedAt'][:10]}\n- Labels: {', '.join(S['pr']['labels']) or '(none)'}\n- Head: {head[:10]} ({S['pr']['head_repo']}:{pr.get('headRefName')})  Base: {base[:10]}\n- Files: {', '.join(files) or '(none)'}")
    md.append("\n### Commits\n" + "\n".join(f"- {c['sha']} [{c['author']}] {c['message']}" for c in S["pr"]["commits"]))
    section("PR body")
    block(body[:8000] or "(empty body)")
    if S["pr"]["comments"] or S["pr"]["reviews"] or S["pr"]["inline_comments"]:
        section("Conversation")
        for c in S["pr"]["comments"]:
            b = c["body"]
            if c["author"] == "netkan-bot" and "automatically generated" in b:
                b = "[bot boilerplate, same as body]"
            md.append(f"**[{c['author']}] {c['date']}**\n\n{b[:3000]}\n")
        for r in S["pr"]["reviews"]:
            if r["body"] or r["state"] != "COMMENTED":
                md.append(f"**[{r['author']}] review {r['state']} {r['date']}**\n\n{r['body'][:3000]}\n")
        for c in S["pr"]["inline_comments"]:
            md.append(f"**[{c['author']}] inline on {c['path']}:{c['line']}**\n\n{(c['body'] or '')[:2000]}\n")

    # 2. file contents -------------------------------------------------------
    section("Changed metadata files (head vs base)")
    S["files"] = []
    head_dir = out / "head"
    base_dir = out / "base"
    for f in pr.get("files") or []:
        path = f["path"]
        entry = {"path": path, "in_netkan_dir": path.startswith("NetKAN/"), "ext": Path(path).suffix}
        if not path.endswith(META_EXT):
            entry["note"] = "not a metadata file"
            S["files"].append(entry)
            md.append(f"- `{path}`: not a metadata file")
            continue
        hc = content_at(args.repo, path, head)
        bc = content_at(args.repo, path, base)
        entry["status"] = "added" if bc is None and hc is not None else "deleted" if hc is None else "modified"
        entry["head"] = hc
        entry["base"] = bc
        if hc is not None:
            p = head_dir / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(hc, encoding="utf-8")
            docs, fmt = parse_yaml_or_json_docs(hc)
            entry["format"] = fmt
            entry["docs"] = docs
            entry["doc_count"] = len(docs)
            entry["identifiers"] = sorted({d.get("identifier") for d in docs if isinstance(d, dict) and d.get("identifier")})
            entry["filename_stem"] = Path(path).stem
            entry["identifier_matches_filename"] = all(i == Path(path).stem for i in entry["identifiers"]) and bool(entry["identifiers"])
            entry["krefs"] = [d.get("$kref") for d in docs if isinstance(d, dict) and d.get("$kref")]
            entry["vrefs"] = [d.get("$vref") for d in docs if isinstance(d, dict) and d.get("$vref")]
            entry["mixed_json_yaml"] = fmt.startswith("yaml") and bool(re.search(r"^\s*\{", hc, re.M)) and bool(re.search(r"^[A-Za-z$_]+\s*:", hc, re.M))
            entry["has_tabs"] = "\t" in hc
            entry["trailing_whitespace_lines"] = len([l for l in hc.splitlines() if l.rstrip() != l])
            entry["ends_with_newline"] = hc.endswith("\n")
            entry["comments_present"] = bool(re.search(r"^\s*#", hc, re.M)) if fmt.startswith("yaml") else False
        if bc is not None:
            p = base_dir / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(bc, encoding="utf-8")
        S["files"].append(entry)
        md.append(f"\n### `{path}` ({entry['status']}; format {entry.get('format', '?')}; {entry.get('doc_count', 0)} document(s); identifiers {entry.get('identifiers')})")
        if hc is not None:
            md.append("Head content:")
            block(hc, "yaml" if entry.get("format", "").startswith("yaml") else "json")
        if bc is not None and hc is not None:
            diff = "".join(difflib.unified_diff(bc.splitlines(True), hc.splitlines(True), "base/" + path, "head/" + path))
            block(diff, "diff")
        elif bc is not None:
            md.append("Base content (file deleted in PR):")
            block(bc)
        for k in ("identifier_matches_filename", "mixed_json_yaml", "has_tabs"):
            if k in entry:
                md.append(f"- {k}: {entry[k]}")

    meta_entries = [e for e in S["files"] if e.get("head") is not None and e["ext"] in (".netkan", ".frozen")]
    primary_ids = sorted({i for e in meta_entries for i in e.get("identifiers", [])}) or [Path(e["path"]).stem for e in meta_entries]

    # 3. CI ------------------------------------------------------------------
    section("CI (Inflate netkans check)")
    ci = ci_info(args.repo, args.pr, not args.no_ci_log)
    S["ci"] = {k: v for k, v in ci.items()}
    if ci.get("inflate") and "log" in ci["inflate"]:
        (out / "ci-inflate.log").write_text(ci["inflate"]["log"], encoding="utf-8")
        S["ci"]["inflate"] = {k: v for k, v in ci["inflate"].items() if k != "log"}
        S["ci"]["inflate"]["log_file"] = str(out / "ci-inflate.log")
    for c in ci.get("checks") or []:
        when = f" (run started {c.get('startedAt')})" if c.get("startedAt") else ""
        md.append(f"- {c.get('name')} [{c.get('workflow')}]: **{c.get('state')}** {c.get('link')}{when}")
    if ci.get("inflate"):
        md.append("CI inflates the release that was newest when the PR was last pushed; compare its version with "
                  "the latest upstream release in the ZIP coverage line below.")
    inf = ci.get("inflate")
    if inf:
        if inf.get("annotations"):
            md.append("\nAnnotations (warnings/errors emitted by the validator):")
            block("\n".join(inf["annotations"]))
        else:
            md.append("\nNo warning/error annotations in the CI log." if "log" in inf else "\n(CI log not downloaded)")
        for name, ck in (inf.get("inflated_ckans") or {}).items():
            md.append(f"\nCI-inflated `{name}`:")
            block(json.dumps(ck, indent=2) if isinstance(ck, dict) else str(ck), "json")
        for name, lst in (inf.get("installed_files") or {}).items():
            md.append(f"\nCI sandbox install listing for **{name}** ({len(lst)} files):")
            block("\n".join(lst))
        for name, lines in (inf.get("groups") or {}).items():
            if name.startswith("Diffing"):
                md.append(f"\nCI diff vs CKAN-meta ({name}):")
                block("\n".join(lines)[:6000], "diff")
        if inf.get("log_error"):
            md.append(f"\nCould not fetch CI log: {inf['log_error']}")
    else:
        md.append("No Inflate check found on this PR. CI has not run: first-time contributors need a maintainer to approve the workflow run, or the PR may be brand new. Rely on the local inflation below.")
    try:
        if inf and inf.get("run_id"):
            art_dir = out / "ci-ckans"
            r = run(["gh", "run", "download", inf["run_id"], "-R", args.repo, "-n", f"metadata-{args.pr}", "-D", str(art_dir)], timeout=300)
            if r.returncode == 0:
                S["ci"]["artifact_dir"] = str(art_dir)
                S["ci"]["artifact_files"] = [p.name for p in art_dir.rglob("*.ckan")]
    except Exception:
        pass

    # 4. local inflation -----------------------------------------------------
    S["local_inflation"] = {}
    ckans_by_file = {}
    if not args.no_inflate and meta_entries:
        section("Local inflation (netkan.exe)")
        exe = ensure_netkan_exe(skill_dir / "bin")
        if not exe:
            md.append("netkan.exe unavailable; skipped local inflation.")
        else:
            for e in meta_entries:
                npath = head_dir / e["path"]
                odir = out / "inflated" / Path(e["path"]).stem
                res = inflate_local(exe, npath, odir, cachedir, args.releases)
                S["local_inflation"][e["path"]] = {k: v for k, v in res.items() if k != "log"}
                (out / f"inflate-{Path(e['path']).stem}.log").write_text(res.get("log", ""), encoding="utf-8")
                ckans_by_file[e["path"]] = res.get("ckans") or {}
                md.append(f"\n### `{e['path']}` -> exit code {res.get('exit_code')}")
                if res.get("error"):
                    md.append(res["error"])
                if res.get("messages"):
                    md.append("Validator messages:")
                    block("\n".join(res["messages"]))
                else:
                    md.append("No WARN/ERROR/FATAL messages from netkan.exe.")
                for name, ck in (res.get("ckans") or {}).items():
                    md.append(f"\nGenerated `{name}`:")
                    block(json.dumps(ck, indent=2), "json")
                if res.get("exit_code") not in (0, None) and not res.get("messages"):
                    block(res.get("log", "")[-3000:])
    # fall back to CI ckans if local inflation produced nothing
    if not any(ckans_by_file.values()) and ci.get("inflate") and ci["inflate"].get("inflated_ckans"):
        for e in meta_entries:
            ckans_by_file[e["path"]] = {k: v for k, v in ci["inflate"]["inflated_ckans"].items() if isinstance(v, dict)}

    # Coverage: CI inflates whatever release was newest when the PR was pushed, and local inflation
    # can FATAL on the newest release (then it yields no .ckan). In both cases the ZIP facts would
    # silently describe an OLD release. Look up the latest upstream release per host and, when no
    # inflated .ckan covers it, analyze that download directly as a LATEST pseudo-ckan.
    def host_latest(d):
        kref = d.get("$kref") or ""
        m = re.match(r"#/ckan/spacedock/(\d+)", kref)
        if m:
            sd = spacedock_info(m.group(1))
            S.setdefault("hosts", {})[f"spacedock/{m.group(1)}"] = sd
            if sd.get("versions"):
                v = sd["versions"][0]
                return {"host": f"spacedock/{m.group(1)}", "version": v.get("friendly_version"),
                        "date": v.get("created"), "url": "https://spacedock.info" + v["download_path"], "note": ""}
            return None
        m = re.match(r"#/ckan/github/([^/]+)/([^/]+)", kref)
        if m:
            rels = gh_api(f"repos/{m.group(1)}/{m.group(2)}/releases?per_page=5") or []
            rels = [r for r in rels if not r.get("draft")]
            if not rels:
                return None
            r0 = rels[0]
            use_src = (d.get("x_netkan_github") or {}).get("use_source_archive")
            am = re.search(r"/asset_match/(.+)$", kref)
            assets = r0.get("assets") or []
            if am:
                assets = [a for a in assets if re.search(am.group(1), a.get("name") or "")]
            # netkan.exe downloads the release ASSET; GitHub's automatic source zipball is used only
            # when x_netkan_github.use_source_archive is set (its <repo>-<sha>/ wrapper rarely has a
            # mod layout). A release with no asset and no use_source_archive cannot be inflated at all.
            if use_src:
                url, note = r0.get("zipball_url"), "use_source_archive: analyzing the source zipball"
            elif assets:
                url, note = assets[0].get("browser_download_url"), ""
            else:
                url, note = None, ("NO RELEASE ASSET: netkan.exe cannot inflate this release (crashes on assets.First()); "
                                   "the author must attach a ZIP, or use_source_archive only if the repo root IS the mod layout, "
                                   "or drop the GitHub document. Not analyzed.")
            return {"host": f"github/{m.group(1)}/{m.group(2)}", "version": r0.get("tag_name"),
                    "date": r0.get("published_at"), "url": url,
                    "note": f"prerelease={r0.get('prerelease')}" + (f"; {note}" if note else "")}
        return None

    def norm_version(v):
        return re.sub(r"^[vV](?=\d)", "", str(v or "")).strip()

    S["coverage"] = {}
    for e in meta_entries:
        docs = [d for d in e.get("docs") or [] if isinstance(d, dict)]
        ident = next((d.get("identifier") for d in docs if d.get("identifier")), None) or Path(e["path"]).stem
        latest = [x for x in (host_latest(d) for d in docs) if x]
        real = [ck for ck in (ckans_by_file.get(e["path"]) or {}).values() if isinstance(ck, dict) and not ck.get("_pseudo")]
        analyzed = sorted({str(ck.get("version")) for ck in real if ck.get("version")})
        local_ok = bool((S["local_inflation"].get(e["path"]) or {}).get("ckans")) and \
            (S["local_inflation"].get(e["path"]) or {}).get("exit_code") == 0
        covered = {norm_version(a) for a in analyzed}
        edits = [d.get("x_netkan_version_edit") for d in docs if d.get("x_netkan_version_edit")]

        def is_covered(v):
            cands = {norm_version(v)}
            for ed in edits:
                try:
                    ev = apply_version_edit(ed, v)
                except re.error:
                    ev = None
                if ev:
                    cands.add(norm_version(ev))
            return bool(cands & covered)

        uncovered = [x for x in latest if x.get("version") and not is_covered(x["version"])]
        if not real:
            uncovered = latest
        cov = {"analyzed_versions": analyzed, "latest_upstream": latest, "local_inflation_ok": local_ok,
               "uncovered": uncovered}
        S["coverage"][e["path"]] = cov
        if uncovered and not local_ok:
            merged_install = next((d.get("install") for d in reversed(docs) if d.get("install")), None)
            for x in uncovered:
                if not x.get("url"):
                    continue  # nothing downloadable (e.g. GitHub release without an asset); the coverage line says so
                name = f"{ident}-LATEST-{x['host'].split('/')[0]}.ckan"
                ckans_by_file.setdefault(e["path"], {})[name] = {
                    "identifier": ident, "version": x["version"], "download": x["url"], "install": merged_install,
                    "_pseudo": True, "_latest": True, "_note": x.get("note", ""), "download_hash": {}}

    # 5. zip analysis --------------------------------------------------------
    S["zips"] = {}
    if not args.no_zip:
        section("Download ZIP analysis")
        for path, cov in S["coverage"].items():
            lu = ", ".join(f"{x['host']} {x['version']} ({(x.get('date') or '?')[:10]}{'; ' + x['note'] if x.get('note') else ''})"
                           for x in cov["latest_upstream"]) or "unknown"
            md.append(f"\nCoverage for `{path}`: inflated .ckan versions available: {cov['analyzed_versions'] or 'NONE'}; "
                      f"latest upstream release: {lu}; local inflation of the latest release: "
                      f"{'OK' if cov['local_inflation_ok'] else 'FAILED or skipped'}")
            if cov["uncovered"]:
                vers = ", ".join(dict.fromkeys(str(x["version"]) for x in cov["uncovered"]))
                md.append(f"**WARNING: no inflated .ckan covers the latest upstream release ({vers}). CI only tests the "
                          "release that was newest when the PR was last pushed, and local inflation produced nothing for "
                          "the current one. The entries marked LATEST UPSTREAM RELEASE below analyze the current downloads "
                          "directly; base install-stanza, `.version`, bundling, dependency and license-file findings on "
                          "THEM. Older entries show only what CI saw.**")
        root = find_repo_root(args.netkan_dir or script_dir)
        local_index, krefs_index, provides_index, refs_index = load_local_index(root) if root else ({}, {}, {}, {})
        seen = set()
        for path, ckans in ckans_by_file.items():
            for name, ck in ckans.items():
                if not isinstance(ck, dict) or ck.get("kind") in ("metapackage", "dlc"):
                    continue
                ident = ck.get("identifier") or Path(path).stem
                urls = ck.get("download") if isinstance(ck.get("download"), list) else [ck.get("download")]
                for url in [u for u in urls if u]:
                    key = (ident, ck.get("version"), url)
                    if key in seen:
                        continue
                    seen.add(key)
                    zpath = find_cached_zip(cachedir, ck)
                    if not zpath:
                        try:
                            zpath = download_zip(url, cachedir)
                        except Exception as ex:  # noqa: BLE001
                            S["zips"][f"{name}|{url}"] = {"error": f"download failed: {ex}"}
                            md.append(f"\n### {name} from {url}\nDownload failed: {ex}")
                            continue
                    z = analyze_zip(zpath, ck, ident, local_index)
                    z["download_url"] = url
                    z["ckan_file"] = name
                    S["zips"][f"{name}|{url}"] = z
                    (out / f"ziplist-{Path(name).stem}.txt").write_text("\n".join(z.get("files") or []), encoding="utf-8")
                    if ck.get("_latest"):
                        md.append(f"\n### LATEST UPSTREAM RELEASE `{ck.get('version')}` ({ck.get('_note') or 'not inflated by CI or local netkan.exe'}) from {url}")
                        md.append("- install approximation below uses the netkan's merged `install` stanza "
                                  "(or the default `find: <identifier>` when none is given)")
                    else:
                        md.append(f"\n### `{name}` version {ck.get('version')} from {url}")
                    if z.get("error"):
                        md.append(z["error"])
                        continue
                    md.append(f"- files: {z['file_count']}  size: {z['size']} bytes  full listing: `{out / ('ziplist-' + Path(name).stem + '.txt')}`")
                    md.append(f"- top-level entries: {z['top_level']}")
                    if len(z["top_level"]) == 1 and re.search(r"-(main|master|[0-9a-f]{7,40})$", z["top_level"][0]) and not z["has_gamedata"]:
                        md.append(f"- **top-level folder `{z['top_level'][0]}` is a GitHub source-archive wrapper**: this download is "
                                  "the repository snapshot, not a packaged mod (release asset made from 'Download ZIP', or "
                                  "use_source_archive). Only a `find` on the inner mod folder installs correctly; a `find: GameData` "
                                  "or `file:` path fails. Worth telling the author to package a proper release.")
                    md.append(f"- has GameData: {z['has_gamedata']}; dirs directly under GameData: {z['gamedata_dirs']}; files directly in GameData: {z['gamedata_root_files']}")
                    if z["nested_gamedata"]:
                        md.append(f"- NESTED GameData inside GameData (install will fail): {z['nested_gamedata'][:5]}")
                    md.append(f"- directory named exactly like identifier `{ident}`: {z['identifier_dir_exact'] or 'NONE'}; case-insensitive-only matches: {z['identifier_dir_ci'] or 'none'}")
                    md.append(f"- DLLs ({len(z['dlls'])}): {z['dlls'][:15]}")
                    md.append(f"- DLL base names: {z['dll_identifiers']}; a DLL matches identifier: {z['dll_matches_identifier']}")
                    if z["source_code"]:
                        md.append(f"- source code files present: {len(z['source_code'])} e.g. {z['source_code'][:5]}")
                    md.append(f"- .version files: {[v['path'] for v in z['version_files']] or 'NONE'}")
                    for v in z["version_files"]:
                        block(json.dumps(v["content"], indent=1) if isinstance(v["content"], (dict, list)) else str(v["content"]), "json")
                    if z["swinfo"]:
                        md.append(f"- swinfo.json (KSP2 SpaceWarp!): {z['swinfo']}")
                    if z["internal_ckan"]:
                        md.append(f"- internal .ckan files: {[c['path'] for c in z['internal_ckan']]}")
                        for c in z["internal_ckan"]:
                            block(c.get("content") or c.get("error", ""))
                    md.append(f"- .cfg files: {z['cfg_count']}; with ModuleManager syntax: {z['modulemanager_syntax_count']} e.g. {z['modulemanager_syntax_files'][:5]}")
                    md.append(f"- heuristic tags from contents: {z['suggested_tags']}; heuristic depends from contents: {z['suggested_depends']}; heuristic suggests: {z['suggested_suggests']}")
                    for note in z.get("version_file_notes") or []:
                        md.append(f"- .version note: {note}")
                    for fo in z.get("find_targets_other_mod") or []:
                        md.append(f"- INSTALL TARGETS ANOTHER MOD'S FOLDER: {fo}")
                    if z["aspect_hits"]:
                        md.append(f"- aspect hits: " + "; ".join(f"`{k}` in {v[:2]}" for k, v in z["aspect_hits"].items()))
                    if z["crafts"]:
                        md.append(f"- craft files ({len(z['crafts'])}): {[(c['path'], c['type']) for c in z['crafts'][:12]]}")
                    if z["ks_scripts"]:
                        md.append(f"- kOS scripts: {z['ks_scripts'][:8]}")
                    if z["patch_files"]:
                        md.append(f"- PatchManager .patch files: {z['patch_files'][:8]}")
                    md.append(f"- license files: {[(l['path'], l.get('guess')) for l in z['license_files']] or 'NONE'}")
                    for l in z["license_files"][:3]:
                        if l.get("head"):
                            block(l["head"][:500])
                    for rd in z["readmes"][:1]:
                        md.append(f"- README `{rd['path']}` head:")
                        block(rd["head"][:800])
                    if z["junk_files"]:
                        md.append(f"- junk/dev files: {z['junk_files'][:12]}")
                    if z["bundled_candidates"]:
                        md.append(f"- BUNDLED third-party mod candidates (should usually be `depends`, not installed): {z['bundled_candidates']}")
                    md.append(f"- approximate install: {z['approx_installed_count']} files -> GameData dirs {z['approx_installed_gamedata_dirs']}; notes: {z['approx_install_notes']}")
                    if not z["approx_installed_count"] and z.get("file_count"):
                        md.append("- **INSTALL STANZA MATCHES NOTHING in this ZIP: netkan.exe fails with "
                                  "'No files found matching find=... to install!' (BLOCKER); pick the folder that exists here**")
                    if z["approx_not_installed_count"]:
                        md.append(f"- approx NOT installed ({z['approx_not_installed_count']}): {z['approx_not_installed'][:25]}")
                    md.append(f"- approx installed DLLs: {z['approx_installed_dlls']}")

    # 6. cross-checks --------------------------------------------------------
    section("Cross-checks against local NetKAN checkout")
    root = find_repo_root(args.netkan_dir or script_dir)
    S["crosscheck"] = {"repo_root": str(root) if root else None}
    if not root:
        md.append("Local NetKAN checkout not found; run from inside the repo or pass --netkan-dir.")
    else:
        local_index, krefs_index, provides_index, refs_index = load_local_index(root)
        gs = run(["git", "status", "--short", "--branch"], cwd=str(root)).stdout.splitlines()
        S["crosscheck"]["git_branch_line"] = gs[0] if gs else ""
        md.append(f"- local checkout: `{root}` ({S['crosscheck']['git_branch_line']}); identifiers indexed: {len(local_index)} (frozen: {sum(1 for v in local_index.values() if v['frozen'])})")
        all_ids_lower = {}
        for k in local_index:
            all_ids_lower.setdefault(k.lower(), []).append(k)
        cc = S["crosscheck"]["per_file"] = {}
        for e in meta_entries:
            docs = [d for d in e.get("docs") or [] if isinstance(d, dict)]
            stem = Path(e["path"]).stem
            r = cc[e["path"]] = {}
            r["exists_on_master_netkan"] = (root / "NetKAN" / f"{stem}.netkan").exists()
            r["exists_on_master_frozen"] = (root / "NetKAN" / f"{stem}.frozen").exists()
            r["case_insensitive_collisions"] = [k for k in all_ids_lower.get(stem.lower(), []) if k != stem]
            r["similar_identifiers"] = [k for k in difflib.get_close_matches(stem, list(local_index.keys()), n=6, cutoff=0.78) if k != stem]
            dup = []
            for d in docs:
                kref = d.get("$kref") or ""
                m = re.match(r"#/ckan/(spacedock|github|gitlab|gitea|sourceforge|jenkins|http|netkan|ksp-avc)/([^'\"\s]+)", kref)
                if m:
                    key = (m.group(1), m.group(2).rstrip("/").lower())
                    if m.group(1) == "github":
                        key = ("github", "/".join(m.group(2).split("/")[:2]).lower())
                    for other in krefs_index.get(key, []):
                        if other != stem:
                            dup.append({"kref": kref, "already_used_by": other, "frozen": local_index[other]["frozen"]})
            r["duplicate_kref"] = dup
            rels = {}
            for key in ("depends", "recommends", "suggests", "supports", "conflicts"):
                names = []
                for d in docs:
                    names += rel_names(d, key)
                if isinstance(docs and docs[-1].get("replaced_by"), dict):
                    pass
                checked = []
                for nme in sorted(set(names)):
                    info = {"name": nme}
                    if nme in local_index and not local_index[nme]["frozen"]:
                        info["status"] = "ok"
                    elif nme in provides_index:
                        info["status"] = f"virtual (provided by {provides_index[nme][:4]})" + (" ; a .frozen file of that name also exists" if nme in local_index else "")
                    elif nme in local_index:
                        info["status"] = "frozen (no live netkan and nobody provides it)"
                    elif nme in DLC_IDS:
                        info["status"] = "dlc"
                    elif nme in primary_ids:
                        info["status"] = "defined in this PR"
                    else:
                        ci_hit = all_ids_lower.get(nme.lower())
                        if ci_hit:
                            info["status"] = f"WRONG CASE (existing: {ci_hit})"
                        else:
                            meta = gh_api(f"repos/KSP-CKAN/CKAN-meta/contents/{nme}")
                            info["status"] = "only in CKAN-meta (no netkan; may be retired/abandoned)" if isinstance(meta, list) else "UNKNOWN identifier"
                            close = difflib.get_close_matches(nme, list(local_index.keys()), n=3, cutoff=0.7)
                            if close:
                                info["did_you_mean"] = close
                    checked.append(info)
                if checked:
                    rels[key] = checked
            r["relationships"] = rels
            r["provides"] = sorted({p for d in docs for p in (d.get("provides") or [])})
            r["referenced_by_other_netkans"] = sorted(refs_index.get(stem, set()) - {stem})[:30]
            dep_names = [x["name"] for x in rels.get("depends", []) if x["status"] in ("ok", "frozen")]
            r["precedents"] = precedents(root, local_index, [d for d in dep_names if d != "ModuleManager"][:3], stem)
            # SpaceDock name search: re-uploads / duplicates under another SpaceDock id
            sd_hits = []
            names_to_search = {stem}
            for d in docs:
                if d.get("name"):
                    names_to_search.add(str(d["name"]))
            m = re.search(r"^Add (.+?) from SpaceDock", pr["title"])
            if m:
                names_to_search.add(m.group(1))
            for q in sorted(names_to_search)[:3]:
                res_ = spacedock_search(q) or []
                for hit in res_:
                    if hit["game_id"] not in (3102, None):
                        continue
                    key = ("spacedock", str(hit["id"]))
                    hit["indexed_as"] = krefs_index.get(key, [])
                    hit["query"] = q
                    if hit not in sd_hits:
                        sd_hits.append(hit)
            r["spacedock_search"] = sd_hits[:12]
            # other OPEN pull requests for the same mod (same file, same identifier, same host)
            open_prs = gh_json("pr", "list", "-R", args.repo, "--state", "open", "--limit", "200",
                               "--json", "number,title,author,files,createdAt") or []
            hosts = set()
            for d in docs:
                m = re.match(r"#/ckan/(spacedock/\d+|github/[^/'\"\s]+/[^/'\"\s]+)", d.get("$kref") or "")
                if m:
                    hosts.add(m.group(1).lower())
            others = []
            for op in open_prs:
                if op["number"] == args.pr:
                    continue
                paths = [f["path"] for f in op.get("files") or []]
                same_file = any(Path(p_).stem.lower() == stem.lower() for p_ in paths)
                title_hit = stem.lower() in re.sub(r"[\W_]+", "", op["title"]).lower()
                host_hit = False
                if hosts and paths and len(others) < 20:
                    for p_ in paths[:3]:
                        c = content_at(args.repo, p_, f"refs/pull/{op['number']}/head") or ""
                        if any(h in c.lower() for h in hosts):
                            host_hit = True
                            break
                if same_file or title_hit or host_hit:
                    others.append({"number": op["number"], "title": op["title"], "author": op["author"]["login"],
                                   "created": op["createdAt"][:10], "files": paths,
                                   "match": [k for k, v in (("same file", same_file), ("title", title_hit), ("same host", host_hit)) if v]})
            r["other_open_prs"] = others
            md.append(f"\n### `{e['path']}`")
            md.append(f"- already exists on master as .netkan: {r['exists_on_master_netkan']}; as .frozen: {r['exists_on_master_frozen']}")
            if r["case_insensitive_collisions"]:
                md.append(f"- CASE-INSENSITIVE identifier collision: {r['case_insensitive_collisions']}")
            if r["similar_identifiers"]:
                md.append(f"- similar existing identifiers (possible duplicate/rename): {r['similar_identifiers']}")
            if dup:
                md.append(f"- DUPLICATE $kref already indexed: {dup}")
            for key, lst in rels.items():
                md.append(f"- {key}: " + ", ".join(f"{x['name']} [{x['status']}{' -> ' + str(x['did_you_mean']) if x.get('did_you_mean') else ''}]" for x in lst))
            if r["provides"]:
                md.append(f"- provides: {r['provides']}")
            if r["referenced_by_other_netkans"]:
                md.append(f"- other netkans referencing `{stem}`: {r['referenced_by_other_netkans']}")
            if r.get("other_open_prs"):
                md.append("- OTHER OPEN PRs for the same mod (one PR per netkan at a time; the older one usually wins unless it is abandoned):")
                for op in r["other_open_prs"]:
                    md.append(f"  - #{op['number']} `{op['title']}` by {op['author']} ({op['created']}), files {op['files']}, matched on {op['match']}")
            if r.get("spacedock_search"):
                md.append("- SpaceDock search results for this mod's name(s) (look for the same mod under another id, other authors' re-uploads, or an already-indexed id):")
                for h in r["spacedock_search"]:
                    md.append(f"  - id {h['id']} `{h['name']}` by {h['author']} (query '{h['query']}'){' ALREADY INDEXED AS ' + str(h['indexed_as']) if h['indexed_as'] else ''}")
            for dep, lst in (r.get("precedents") or {}).items():
                if lst:
                    md.append(f"\nPrecedent netkans that also depend on `{dep}` (house style for install/tags):")
                    for p in lst:
                        md.append(f"`{p['identifier']}`:")
                        block(p["netkan"], "yaml")

    # 7. hosts ---------------------------------------------------------------
    section("Upstream host data")
    S["hosts"] = {}
    for e in meta_entries:
        for d in [d for d in e.get("docs") or [] if isinstance(d, dict)]:
            kref = d.get("$kref") or ""
            m = re.match(r"#/ckan/spacedock/(\d+)", kref)
            if m and f"spacedock/{m.group(1)}" not in S["hosts"]:
                sd = spacedock_info(m.group(1))
                S["hosts"][f"spacedock/{m.group(1)}"] = sd
                md.append(f"\n### SpaceDock mod {m.group(1)}")
                block(json.dumps(sd, indent=1), "json")
            m = re.match(r"#/ckan/github/([^/]+)/([^/]+)", kref)
            if m and f"github/{m.group(1)}/{m.group(2)}" not in S["hosts"]:
                gh = github_info(m.group(1), m.group(2), d.get("x_netkan_version_edit"))
                gh["x_netkan_github"] = d.get("x_netkan_github")
                gh["kref_options"] = kref.split("/")[5:] if kref.count("/") > 4 else []
                S["hosts"][f"github/{m.group(1)}/{m.group(2)}"] = gh
                md.append(f"\n### GitHub {m.group(1)}/{m.group(2)}")
                block(json.dumps(gh, indent=1), "json")
            m = re.match(r"#/ckan/netkan/(.+)", kref)
            if m and f"metanetkan/{m.group(1)}" not in S["hosts"]:
                remote = try_http_get(m.group(1))
                S["hosts"][f"metanetkan/{m.group(1)}"] = {"content": remote}
                md.append(f"\n### Metanetkan {m.group(1)}")
                block(remote or "(fetch failed)")
            m = re.match(r"#/ckan/(gitlab|gitea|sourceforge|jenkins|http|ksp-avc)/(.+)", kref)
            if m:
                md.append(f"\n### {m.group(1)} kref: {m.group(2)} (not auto-inspected; check manually)")
    for ident in primary_ids:
        st = status_entry(ident, persist)
        S["hosts"][f"status/{ident}"] = st
        md.append(f"\n### CKAN status page entry for `{ident}`")
        block(json.dumps(st, indent=1) if st else "not present on status page (not yet indexed)", "json")

    # write ------------------------------------------------------------------
    (out / "facts.md").write_text("\n".join(md), encoding="utf-8")

    def default(o):
        if isinstance(o, (set,)):
            return sorted(o)
        if isinstance(o, Path):
            return str(o)
        return str(o)
    slim = json.loads(json.dumps(facts, default=default))
    for e in slim["sections"].get("files", []):
        e.pop("head", None)
        e.pop("base", None)
    for z in slim["sections"].get("zips", {}).values():
        z.pop("files", None)
        z.pop("approx_installed_files", None)
    (out / "facts.json").write_text(json.dumps(slim, indent=1), encoding="utf-8")
    print(str(out / "facts.md"))


if __name__ == "__main__":
    main()
