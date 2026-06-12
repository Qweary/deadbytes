# Dead Bytes Tell No Lies — ToorCamp 2026

A ToorCamp 2026 conference package on exploiting the **Alarm Lock Trilogy T2/T3** access-control lock. It has two sides: a conference **talk** that walks the five-layer attack chain, and a hands-on **workshop** where attendees clip a flash programmer onto a real lock's DataFlash chip, decode the user-code page, inject their own codes, and watch the lock open.

## Two sides — start here

| Side | What it is | Open this |
|---|---|---|
| **`talk/`** | The conference talk — a reveal.js slide deck plus speaker materials covering the five-layer attack chain (physical, DataFlash, firmware, USB-cable, audit-trail). | [`talk/README.md`](talk/README.md) |
| **`workshop/`** | The hands-on flash-programmer workshop — facilitator guide, participant handout, a DataFlash decode reference, and a one-command build kit for the station laptops. | [`workshop/README.md`](workshop/README.md) |

If you are new here and want the quickest path:

- **Watching the talk?** Open `talk/index.html` in any modern browser.
- **Attending the workshop?** Clone this repo and run one command from the repo root — `./bin/start.sh` (Windows: `start.ps1`). The browser opens to a local READ/WRITE control panel in Practice mode (sample copy, no hardware); a Live-lock tab drives the real chip behind an in-browser confirmation. No setup, no `sudo` — the kit even bundles a Linux `minipro` **and its device database** (`workshop/kit/share/minipro/`), found automatically via `workshop/kit/bin/minipro-env.sh`, so a station laptop needs nothing installed and resolves chip profiles out of the box. The `workshop/PARTICIPANT-HANDOUT.md` card has the one command plus a CLI fallback (`python3 workshop/kit/tools/lock-tool.py read --all` from the repo root).
- **Running the workshop?** Start with `workshop/README.md`, then `workshop/FACILITATOR-GUIDE.md` for the staffed-station operations reference.

## Author / further reading

By **qweary**.

- Blog series: **`qweary.github.io`** — the "Dead Bytes Tell No Lies" write-ups and other access-control research.
- GitHub: **`github.com/qweary`** — all the repos.
- T2/T3 lock research repo: **`github.com/Qweary/T2-T3-Lock-Exploitation-Research`** — code, dumps, handwritten notes, and the full blog series.

## License

See [`LICENSE`](LICENSE).
