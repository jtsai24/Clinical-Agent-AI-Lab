# Production gaps

Tracks where this project's rehearsal/prototype choices diverge from what a real production deployment would need, per [#7](../../issues/7) step 7. Filled in incrementally as each gap is actually hit, not written speculatively up front.

## Secrets / API key handling

**Current (rehearsal):** local `.env` file (gitignored, `chmod 600`), loaded at runtime via `python-dotenv`. One key per project, generated manually in the provider's dashboard.

**Production best practice:**

A secrets manager's automation doesn't apply equally everywhere — it depends on which side of the trust boundary a given credential sits on.

- **Internal, within-your-infra relationships** (service → vault, service → database, service → another internal service) can use short-lived, auto-issued credentials, because the credential issuer is inside a trust boundary your own platform controls. AWS can attest "this request really came from the Lambda I provisioned," so it can hand out a 15-minute STS token instead of a static password — via an IAM role, a service account, or workload identity federation. This is where a secrets manager's dynamic leasing, auto-rotation, and revocation genuinely eliminate static secrets, because the issuer participates in the mechanism.
- **The boundary to the LLM provider is not that kind of relationship.** Together AI (or Anthropic, OpenAI) has no way to attest which of your workloads a request came from — it only recognizes a bearer token it issued. Essentially no commercial LLM provider supports identity federation today. So that credential is irreducibly a long-lived static secret from this system's point of view: something has to be its root holder. That's either a human operator who provisions it once and writes it into the vault, or an automation identity (e.g. a CI job calling the provider's account-management API) that needs its *own* long-lived credential to do the provisioning — pushing the same problem up one level rather than resolving it.
- **What the secrets manager actually buys at that specific boundary**, given the static key can't be eliminated: encryption at rest (optionally behind an HSM/KMS so plaintext never touches ordinary storage), restricting which identities may read it, logging every read, and rotating it on whatever cadence the provider supports — without having to chase down every service that held a copy, since every consumer re-fetches from one place instead of being handed the key directly.
- **Runtime hygiene either way:** hold the key in memory only, never write it to disk or logs — redact it in structured logging, error messages, and crash reports (a stack trace dumping `os.environ` is a common real leak vector), and never pass it as a CLI arg (visible in `ps`/shell history).
- **Detection:** secret-scanning on every commit/PR (GitHub secret scanning, `gitleaks`, `trufflehog`) as a backstop for the inevitable human mistake, plus alerting if a scanner or the provider flags a key as publicly exposed.
- **Audit:** access to the secrets store is logged (who/what fetched which secret, when) — relevant in a clinical/compliance context, since an auditor may ask what had access to a key that could reach patient data.

**The gap, concretely:** local `.env` + `python-dotenv` → the key held in a managed secrets store instead of a file on disk, with access restricted and logged, and rotated on a schedule. This moves *handling* of the static credential to a safer place; it does not, and cannot, make the credential itself short-lived — that floor is set by the LLM provider's own auth model, not by anything on this project's side.

## Other gaps (to fill in as the build proceeds)

- Retries, backoff, rate limiting on LLM calls.
- Cost and latency tracking per call.
- Larger evals beyond the 50-row cap; model comparison.
- PHI handling (this prototype uses only public PubMedQA abstracts — no real patient data; a real deployment would need a BAA with the model provider before sending any PHI, and audit logging of what was sent).
- Monitoring / alerting on reject rate and accuracy drift.
- Human review workflow for rejected rows.
