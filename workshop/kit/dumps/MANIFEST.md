# dumps/ — sub-manifest

Sensitive content. The `.bin` files here derive from a captured memory image of a real Alarm Lock T2/T3 lock board. Two ship: the code-free canonical recovery baseline, and a teaching sample (the baseline with the three default workshop codes injected additively). See `../docs/DATAFLASH-DECODE-REFERENCE.md` for the dump format + validation reference.

| File | Size (bytes) | MD5 | Provenance |
|---|---:|---|---|
| `intact-lock-AT45DB041E-main-2026-05-20.bin` | 540672 | `eb6acff32ef13b29ac6ebed10d77316d` | canonical intact-lock baseline; two independent bench reads byte-identical to this MD5; used as recover-baseline.py default; code-free so the MD5 recovery gate is never corrupted; AT45DB041E main array (2048 pages * 264 bytes) |
| `workshop-sample-3codes-AT45DB041E-2026-05-20.bin` | 540672 | `741dcc79d9975b956d9e1c0a14de0e2b` | teaching sample: canonical baseline + the 3 default workshop codes injected additively at slots 19/32/49 (133769 Master / 420420 Elevated / 696969 Supervisor); default READ source for decode-codes.py and lock-tool.py; AT45DB041E main array (2048 pages * 264 bytes) |
