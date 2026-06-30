# Security and Responsible Use

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository when available. Do not publish candidate data, credentials, exploit details, or personally identifiable information in a public issue.

## Security model

The release path is designed for offline, deterministic execution. It validates the input artifact, model artifact, configuration, candidate count, numeric outputs, and final CSV hash before publication. The container uses a digest-pinned base image and hash-pinned Python dependencies. The API exposes separate health and readiness endpoints and applies request-size, candidate-count, timeout, concurrency, CORS, and security-header controls.

## Data handling

- Run only on candidate data you are authorized to process.
- Do not commit challenge data, personal data, API keys, or generated candidate exports.
- The full 100,000-candidate challenge pool is never committed (`.gitignore`d). The committed API
  showpiece (`apps/api/data/precomputed.json`) replays only this submission's own published top-100 for
  the live demo, with personal-identity, contact-verification, and compensation fields redacted; the
  underlying pool is synthetic challenge data, not real individuals.
- Treat ranking explanations and integrity flags as decision support, not verified facts about a person.
- Retain human review for consequential hiring decisions and provide an appropriate appeal or correction path.

## Supported release

Security fixes target the latest release on the default branch. Historical experiment branches and research artifacts are retained for auditability but are not deployment targets.
