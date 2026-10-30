---
name: artifact-delivery-integrity
description: Finalize and verify generated delivery artifacts after builds, exports, reviews, signing, optimization, or independent verification. Use for APKs, installers, archives, executables, PDFs, media exports, and other production deliverables.
metadata:
  hermes:
    tags: [delivery, integrity, verification, release, evidence]
---

# Artifact Delivery Integrity

Use this skill whenever a task produces a binary or generated artifact whose identity can change during BUILD, EXPORT, or REVIEW.

## Core invariant

The artifact produced by the **last artifact-writing action** is the only artifact that may be declared final. Earlier hashes, sizes, metadata, screenshots, and reports are provisional.

## Workflow

1. Identify every action that can rewrite the deliverable: build, export, signing, packaging, optimization, formatting, metadata injection, or independent verifier commands.
2. Let the independent verifier inspect and, when useful, reproduce the build. Treat a verifier report as evidence, not as proof that the pre-review artifact remained unchanged.
3. After REVIEW, recompute the final artifact identity:
   - exact path;
   - byte size;
   - SHA-256 or appropriate cryptographic digest;
   - package/format metadata;
   - required embedded files or assets;
   - signature or build type when applicable.
4. Re-run cheap final gates appropriate to the artifact.
5. Compare the post-review identity with every report and handoff manifest. Update stale values or record an explicit match result.
   - Avoid archive self-reference: freeze all files that belong inside the archive first, build and hash the archive once, then write the archive's hash to a manifest **outside** that archive. If an embedded report must contain the archive hash, define a detached manifest/signature instead of rebuilding the archive in a hash-changing loop.
   - After hashing, do not modify or recopy the artifact. Verify the manifest by reading the current files and checking both byte size and digest equality.
6. Regenerate visual evidence after the final UI/font/layout/export change. Inspect the actual pixels for glyphs, clipping, overflow, target size, and responsive layout.
7. Attach observed evidence to required atomic checklist leaves. Complete parents only through verified leaf roll-up.
8. Distinguish artifact completion from environment-dependent verification. Device launch, live credentials, external APIs, production signing, and publication remain explicit limitations unless actually tested.

## Independent verifier contract

- Give the verifier exact artifact paths, required metadata, expected package identity, and prohibited external effects.
- Ask for PASS/FAIL/REMAINING with file-backed evidence.
- If the verifier rebuilds or exports, run the final identity check again after it returns.
- Never cite the verifier's self-report alone for external side effects or artifact identity.

## Reporting contract

The final report must contain:

- final path, byte size, hash, version/package metadata;
- build/test results and log paths;
- independent review result;
- visual evidence paths when applicable;
- security/secret-scan result when applicable;
- explicit unverified or unintegrated limitations;
- confirmation that report values match the current artifact.

## Checklist discipline

- Evidence belongs on each required atomic leaf, not only on its parent.
- Adapter boundaries and DEMO states may satisfy an adapter-contract leaf, but never count as proof of live service configuration.
- A static rule inspection is not an emulator or production-service test; label it accurately.
- A Gradle task reported as `NO-SOURCE` means no unit-test source was executed; report lint/build/package success separately instead of claiming unit tests passed.
- For source archives, verify CRC, duplicate/path-traversal entries, an explicit secret/cache/browser-profile denylist, and a bounded sensitive-pattern scan before delivery.
- Preserve verified sibling leaves when repairing one failed branch.
- After visual QA, stop only project-owned temporary servers and browser/CDP process trees, then verify their ports and profiles are no longer active; never close unrelated user browser sessions.

## Pitfalls

- Do not assume an up-to-date build is non-mutating.
- Do not keep a pre-review hash after a verifier has run build/export commands.
- Do not inspect a screenshot made before the last CSS/font/layout correction.
- Do not convert missing devices or credentials into false PASS claims.
- Do not bulk-complete a hierarchy before required leaves have evidence.

## Supporting references

- See `references/post-review-finalization.md` for a concise cross-artifact final-gate checklist and Android APK example.
- See `references/android-webview-mobile-delivery.md` when an Android WebView app needs mobile-only layout proof, exact-viewport receipts, embedded-asset verification, unsigned release handling, secret-safe source ZIP creation, or QA-process cleanup.
