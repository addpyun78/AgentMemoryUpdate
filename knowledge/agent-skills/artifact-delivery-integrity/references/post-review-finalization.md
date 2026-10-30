# Post-review finalization checklist

## Cross-artifact gate

Run after the last reviewer, build, export, signer, or optimizer:

- [ ] Final output path exists and is the intended deliverable.
- [ ] Byte size is recorded.
- [ ] SHA-256 is recomputed.
- [ ] Format/package metadata is inspected with a native tool.
- [ ] Required embedded assets are inventoried.
- [ ] Latest build and test outputs are read, not merely assumed.
- [ ] Final screenshots were generated after the last visual change.
- [ ] Reports/manifests contain the current hash, size, and metadata.
- [ ] Independent review findings are resolved or listed as remaining.
- [ ] Device, account, credential, network, signing, and publishing limitations are explicit.
- [ ] Required atomic checklist leaves have concrete evidence before parent completion.

## Android APK example

A useful final APK gate includes:

1. `sha256sum` and byte size of the exact APK path.
2. `aapt dump badging` for application ID, version, min/target SDK, label, and launchable Activity.
3. APK archive inventory for required assets and confirmation that prohibited large models or secrets are absent.
4. Latest Gradle build and unit-test result.
5. WebView security inspection when applicable: trusted asset origin, file/content access policy, mixed content, external navigation, and subresource blocking.
6. Final viewport screenshots after the last CSS/font fix.
7. Connected-device or emulator install/launch result. If unavailable, say `not verified`; do not imply runtime launch.
8. Final report reconciliation: compare the current APK hash with the documented hash and emit an explicit match/mismatch result.

## Evidence wording

Prefer precise labels:

- `static contract PASS` rather than `service integration PASS` when only rules/config were inspected;
- `DEMO adapter boundary verified` rather than `Google/Firebase connected` when credentials are absent;
- `APK build/package PASS; device launch not verified` when no device or emulator was used;
- `post-review hash matches report` when the final digest was compared after verifier activity.
