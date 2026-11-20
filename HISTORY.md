# Repository history and migration

This private repository continues the static MAMUT-routing specification originally stored in `mamut-routing-standard/` within `0nyr/phd-reports`. Onyr requested its migration with Git history on 26 October 2026 during session s123. Public release, a MAMUT-routing submodule and website documentation are deferred to the work tracked in plan21.

## Original history

The directory had 1 committed revision before extraction:

| Original report commit | Extracted repository commit |
|---|---|
| `26972706f9fec4dda1350a17c33b4f28de19494e` | `3317ece848d6d24b64db58844d2bc44805c2bcc3` |

The extraction uses `git subtree split --prefix=mamut-routing-standard HEAD`. It preserves the directory's committed tree, author identity, author date, commit message and existing coauthor trailer. The commit identifier changes because the directory becomes the repository root. Unrelated report history is excluded.

## Current draft revisions

Commit `b5ace30` preserves the uncommitted source reorganization, first-use terminology links, public-facing results, release-scope ruling, current review PDF and existing validation records. The numerical reference and conformance-test contents are unchanged. The standalone repository then adapts its README and build-file exclusions and records focused migration verification.

The complete original directory, including ignored generated files, was archived locally before migration. Every file was transferred byte for byte before repository setup edits. The original report history remains intact. Historical provenance and validation records are preserved as evidence for their recorded snapshots. Pre-existing external-source hash mismatches remain explicit.

No benchmark revision, BKS, production checker or website was migrated by this repository move. The document's author list remains a draft attribution, with review and approval pending.

## November review draft

The 20 November 2026 local review copy incorporates the later static amendments to the report checkout (including materialization, proof provenance and the native evidence appendix) and the joint static and TD draft from session 129. The LaTeX inputs, companion sources and review PDF are synchronized with the report source. The October migration and evidence records describe their original snapshots.
