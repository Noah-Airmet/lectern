# Lectern

A public-domain library of Latter-day Saint and Christian scholarship, searchable and
citable to the page: <https://lectern.restorationcommons.org>. Part of
[Restoration Commons](https://restorationcommons.org).

352 books printed before 1931: the Journal of Discourses and the first doctrinal works of the
Restoration, the Schaff Church Fathers, the first Loeb Classical Library volumes, the
Septuagint and the Greek New Testament, Josephus, commentaries and lexicons. Every page can be
searched, read, linked and quoted, and a quotation can be checked against the page it cites.
It is also an MCP server, so an AI assistant can do the same:

```sh
claude mcp add --transport http lectern https://lectern-api.restorationcommons.org/mcp
```

A citation is a book, a scan and a page: `npnf2:04-select-works-and-letters/r1/p65`, or as a
link, `https://lectern.restorationcommons.org/d/npnf2/04-select-works-and-letters/r1/p65`.

## How it is built

Lectern runs on the engine behind Catchword (`Noah-Airmet/safetypage`): its citation scheme,
storage, quote check, keyword search, snapshot builder and MCP server, used as a library and
pinned to one commit (`ARG ENGINE` in `build/Dockerfile` and `deploy/Dockerfile`; keep the two
the same). This repository holds only what is Lectern's own.

| | |
|---|---|
| `shelf/volumes.jsonl` | The shelf: one row per book, with its id, catalogue record, shelf, series, and the evidence that it is in the public domain. Each row names its scan by the SHA-256 of the file. `shelf/README.md` says how the list was made. |
| `shelf/links.md` | The plan for linking beyond the books: which journals and archives go in, in which tier, and which need a note to the owner first. The research behind it is in `shelf/sources/`. |
| `build/ingest.py` | Reads each scan (text and word boxes per page, with the engine's PDF reader) into the working corpus as one version with its licence fact. |
| `build/render.py` | Draws page images into the snapshot builder's cache ahead of the build. |
| `build/snapshot.py` | Seals a snapshot: keyword index, public files, page images. |
| `library/` | What the MCP server says about itself: its name (`library.toml`) and the four tools' descriptions. |
| `deploy/` | The API origin on VM 100: the server and a Caddy file server (`compose.yaml`). |
| `site/` | The website (Astro, static), forked from Catchword's site. Its home page is the Gospel Scholar Archives' (the wall of books, the Field, the composer) with Lectern's books; the wall's books are listed in `site/src/lib/wall.ts`. |

## Building

The scans live on the homelab (VM 100), so the build runs there, in Docker, with the work in
`/data/lectern`. From a clone of this repository at `/opt/lectern`:

```sh
docker build -f build/Dockerfile -t lectern-build .
docker run --rm -v /data:/host/data:ro -v /data/lectern:/work lectern-build \
  python build/ingest.py --shelf shelf/volumes.jsonl --prefix /host \
    --catalog /host/data/research-corpus/manifests/catalog.sqlite --work /work
docker run --rm -v /data/lectern:/work lectern-build python build/render.py --work /work
docker run --rm -v /data/lectern:/work lectern-build python build/snapshot.py --work /work <id>
```

Snapshot ids are `YYYY.MM.N` and never reused. The corpus is about 4 GB and the page images
about 17 GB; rendering takes a few hours on three cores.

## Serving

`deploy/compose.yaml` on VM 100 (project `lectern`, `127.0.0.1:8096`), behind the `gsa-dash`
tunnel as `lectern-api.restorationcommons.org`, with a Cloudflare cache rule for its `/data/`
files. `deploy/serve.sh <id>` (on VM 100, from `/opt/lectern`) puts a sealed snapshot's files
at `/data/<id>/` and moves search and MCP to it. Older snapshots' files stay served, so the
site keeps working until it is rebuilt on the new one.

The site reads a few of the snapshot's files at build time and asks the live server for the
landing page's quote check:

```sh
cd site && npm install
scripts/fetch_data.sh <id>      # the cards, first pages and example book, into .snap/
SAFETYPAGE_PUBLIC_DIR=.snap/public SAFETYPAGE_API=https://lectern-api.restorationcommons.org \
  SITE_URL=https://lectern.restorationcommons.org PUBLIC_API_BASE=https://lectern-api.restorationcommons.org \
  npx astro build
rsync -a records/ homelab:/data/lectern/records-tmp/ && ssh homelab 'cd /data/lectern && for b in records-tmp/*; do d="served/records-${b#records-tmp/}"; if [ -e "$d" ]; then rm -rf "$b"; else mv "$b" "$d"; fi; done'
npx wrangler@4.156.0 pages deploy dist --project-name lectern --branch main --commit-dirty=true
```

Cloudflare Pages takes at most 20,000 files a deployment, so the articles' record pages are not
in `dist/`: the build moves them to `records/<build>/`, which goes up to the API origin as
`/data/records-<build>/` (the `rsync` line), and the edge rule (`edge/worker.js`) fetches one
from there when Pages has no file for it. The books' record pages stay in `dist/`.

The site is the Cloudflare Pages project `lectern` at `lectern.restorationcommons.org`.
`ui-check` (config in `site/`) checks it; serve `dist` with `node scripts/serve.mjs dist 4412`.
