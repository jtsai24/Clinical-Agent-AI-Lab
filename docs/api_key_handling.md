# API key handling: prototyping vs. production

General reference distilled from working through Stage 1's Together AI credential ([#8](../../issues/8)). Two tiers: what's appropriate while prototyping on one developer's machine, and what changes once this leaves that context.

## Prototyping: why an environment variable

The question isn't "is an env var secure" in the abstract — it's "where should a secret live while a program runs," compared against the realistic alternatives:

- **Hardcoded in source — never.** In every clone, every commit forever (even after deletion), visible to anyone with repo read access.
- **Committed config file — same problem as hardcoding.** `.gitignore`-ing it afterward doesn't erase it from history if it was ever committed.
- **CLI argument (`--api-key=xxx`) — avoid.** Lands in shell history, and on most systems another local user can see a running process's full command line (`ps aux`, `/proc/<pid>/cmdline`) — unlike environment variables, args aren't restricted to the owning user.
- **Environment variable — the pragmatic default.** Universal convention (every SDK/CLI/language reads credentials this way, no custom parsing code needed), confined to the process's own memory rather than disk, and OS-protected by the same mechanism that protects a process's memory in general.

### The actual OS mechanism (not just "permission protected")

An environment variable isn't a separate OS resource with its own ACL — it's data sitting inside the owning process's own memory, so it inherits whatever rule already governs "can process A inspect process B":

- **Linux:** exposed via `/proc/<pid>/environ`; reading it requires the same UID as the target process, or root / `CAP_SYS_PTRACE`. Two processes running as *you* can read each other's environment — that's not a privilege escalation, it's just common ownership.
- **macOS** (what this project runs on): stricter by default. Even same-UID inspection additionally requires the inspecting tool to hold specific entitlements (e.g. `get-task-allow`), due to System Integrity Protection and the hardened runtime — same-user access isn't automatically granted the way it is on Linux.

For this project: a local `.env` file (`chmod 600`, gitignored), loaded at process start via `python-dotenv`. `chmod 600` means only the file's *owner* can read/write it; the running process shares that owner's UID (you're not running as root), so the kernel permits the read via plain ownership match, not elevated privilege.

### What this setup does and doesn't defend against

**Covers:** accidental git commit, other local user accounts on the same machine, the key never appearing in source code, CLI args, or shell history.

**Doesn't cover:** root/sudo access, disk-level compromise (unencrypted disk, stolen laptop), malware running as the same user, accidental logging/printing of the key, no rotation, no audit trail, and it doesn't scale past one developer on one machine.

**The real caveat worth naming, even here:** environment variables are inherited by every *child* process spawned from the one holding them. If a pipeline ever shells out to another tool, that child gets a copy of the whole environment block. Not a live risk in this project (nothing spawns subprocesses), but it's the honest gap, not "env vars are secure, full stop."

The calibration that matters: this handling matches the actual threat model (one trusted developer, one machine, no subprocess spawning, no cloud console exposure) — it is not an attempt to be production-grade, and it doesn't need to be yet.

## Production: see [production_gaps.md](../production_gaps.md)

The production tier isn't just "use a secrets manager" — that claim needs a boundary drawn on it:

- **Internal, within-your-infra relationships** (service → vault, service → database) can use short-lived, platform-attested credentials (IAM roles, workload identity, STS tokens), because the credential issuer is inside a trust boundary your own platform controls. This is where a secrets manager's automation — dynamic leasing, auto-rotation, revocation — genuinely eliminates static secrets.
- **The boundary to the LLM provider is not that kind of relationship.** Together AI (like Anthropic, OpenAI) has no way to attest which of your workloads a request came from — it only recognizes a bearer token it issued, and essentially no commercial LLM provider supports identity federation today. That credential is irreducibly a long-lived static secret from this system's side; something has to be its root holder.
- **What a secrets manager actually buys at that specific boundary:** encryption at rest, restricting which identities may read it, logging every read, and rotating it on whatever cadence the provider allows — without redistributing a new key to every service that held a copy. That's centralized authorization, rotation, and audit on the downstream key — not the elimination of authentication to reach the vault in the first place.

Full detail, including runtime hygiene and detection practices, is in [production_gaps.md](../production_gaps.md)'s "Secrets / API key handling" section.
