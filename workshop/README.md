# Workshop — Dead Bytes Tell No Lies

The hands-on companion to the talk. Attendees decode the user-code page of an Alarm
Lock T2/T3's AT45DB041E DataFlash chip, inject their own codes additively, and — on the
opt-in live path — watch the lock open with a code they just forged.

## Attendees — one command

From the cloned repo root:

```bash
./bin/start.sh
```

The browser opens to a local READ/WRITE control panel. That's the whole workshop — no
hardware, no setup, no `sudo`. (Windows: `start.ps1` from the repo root.) The
**`PARTICIPANT-HANDOUT.md`** attendee card has the one command, a CLI fallback, and the
short teaching essence. That handout plus the GUI is everything an attendee needs.

### CLI fallback (no browser)

The same READ/WRITE run straight from the clone, from any directory, with no `sudo`:

- `python3 workshop/kit/tools/lock-tool.py read --all` — decode all 50 slots (the
  default source carries three baked-in codes, so you see real codes immediately).
- `python3 workshop/kit/tools/lock-tool.py write --code 420420 --slot 32 --role elevated`
  — bake your own code into a copy additively and re-decode it so you watch it land.
- `python3 workshop/kit/tools/recover-baseline.py` — restore the code-free baseline.

The live-chip path is the advanced, confirmation-gated opt-in (`lock-tool.py ... --live`,
`sudo`-free via the bundled udev rule); everything defaults to the safe sample-dump-copy
path.

---

## For organizers — building & standing up a station

The rest of this README is organizer-oriented: building and verifying the kit, standing up a station laptop, and editing the source docs. **A pure attendee does not need any of it** — clone the repo, run `./bin/start.sh`, and follow `PARTICIPANT-HANDOUT.md`. The full staffed-station operations reference — recovery, dump production, hardware counts, troubleshooting — lives in **`FACILITATOR-GUIDE.md`**; attendees never open it.

### Build and verify the kit

The kit is built and validated from `kit/`. Run these from the kit directory:

1. Assemble the kit from its source files. This copies the latest facing docs, the decode reference, and the Python tools into the kit, then regenerates the manifests. From the repo root:

   ```
   cd workshop/kit
   make assemble
   ```

   The command prints `==> Assembly complete.` on success.

2. Verify kit integrity. This MD5-checks every kit file against `MANIFEST.md` and exercises both Python tools' self-test modes. It is hardware-free — no T48 programmer or USB device required.

   ```
   make selftest
   ```

   The run must end with `selftest RESULT: PASS` and `Checked: 19 files`.

3. (Optional) Build the distributable tarball. This produces a reproducible `facilitator-kit-toorcamp-2026.tar.gz` one level up, in `workshop/`.

   ```
   make tarball
   ```

   Two consecutive `make tarball` runs produce byte-identical output. Run `make clean` to remove the built tarball, or `make help` to list all targets.

### Stand up a station laptop

On a fresh Kali laptop, drop the tarball, extract it, and run the installer:

```
tar -xzf facilitator-kit-toorcamp-2026.tar.gz
cd facilitator-kit-toorcamp-2026
sudo ./install.sh
```

After `install.sh` completes, `minipro` is on `$PATH` and the T48 udev rules are installed — including `61-minipro-uaccess.rules` (`TAG+="uaccess"`), which grants the logged-in user access to the programmer directly. There is **no** `plugdev`/`groupadd`/log-out-log-in dance: the live read/write path is `sudo`-free. Root is needed only for `install.sh` itself (the binary drop to `/usr/local/bin` and the udev rule install + reload). The installer exercises every Python tool's self-test as its final smoke gate and exits non-zero on any failure. See `kit/README.md` for the full stand-up walkthrough, the recovery workflow, and known limitations.

#### One command from a fresh clone

If you would rather not `cd` into the kit, the repo root ships a single bootstrap that assembles, verifies, and stands up the station in one go. From the cloned repo root:

```
sudo ./bootstrap.sh
```

It is path-relative — clone the repo anywhere and run it; nothing hardcodes a home directory. The same end-to-end stand-up is available from the kit as `make station`.

### Editing the docs — edit the sources, not the kit copies

`kit/docs/` and `kit/tools/` are **build outputs**. `make assemble` regenerates them by copying from the source files in `workshop/` and `workshop/src/`:

| Edit this source | Regenerated kit copy |
|---|---|
| `workshop/FACILITATOR-GUIDE.md` | `kit/docs/FACILITATOR-GUIDE.md` |
| `workshop/PARTICIPANT-HANDOUT.md` | `kit/docs/PARTICIPANT-HANDOUT.md` |
| `workshop/src/DATAFLASH-DECODE-REFERENCE.md` | `kit/docs/DATAFLASH-DECODE-REFERENCE.md` |
| `workshop/src/build-injected.py` | `kit/tools/build-injected.py` |
| `workshop/src/recover-baseline.py` | `kit/tools/recover-baseline.py` |

After editing any source, re-run `make assemble && make selftest` from `kit/` so the kit copies and their MD5 manifests stay current. Never hand-edit a file under `kit/docs/` or `kit/tools/` — the next `make assemble` will overwrite it.
