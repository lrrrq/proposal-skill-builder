# Worktree Cleanup Handoff — 2026-05-29

## Handoff Note

- Time: 2026-05-29 13:10 Asia/Shanghai
- Author: Codex
- Platform: Codex Desktop
- Repo: `/Applications/lrq/coding/proposal-skill-builder`
- Branch: `codex/cli-command-slimming`
- Status: cleanup completed, worktree cleaned

## Why This Cleanup Was Needed

The repository had accumulated mixed changes from multiple model runs:

- source code cleanup
- generated pipeline outputs
- generated reports
- draft/published skill artifacts
- unreviewed helper scripts
- source proposal file movement/deletion

These categories have different review and commit rules. Keeping them in one dirty worktree makes it impossible for the next model to know what is intentional, what is generated, and what is safe to commit.

The cleanup separated these categories without deleting the recoverable work.

## Safety Snapshot

Before cleanup, the current dirty state was saved outside the repo:

```text
/tmp/proposal_dirty_status_2026-05-29.txt
/tmp/proposal_dirty_diff_2026-05-29.patch
/tmp/proposal_untracked_2026-05-29.txt
```

These files are diagnostic snapshots only. They are not part of the repository.

## Already Committed Before This Cleanup

Two relevant cleanup commits were already present when this pass started:

```text
4230850 Remove unused imports and consolidate duplicate _load_json utility
6f7664e Add project agent instructions and gitignore updates
```

Meaning:

- The 10-file source cleanup is already committed.
- `AGENTS.md` and `.gitignore` updates are already committed.
- This pass did not re-commit those changes.

## Stashes Created

Three stashes were intentionally kept.

### 1. Source Proposal Movements

```text
stash hash: db08a940afa00ec5adefd4fece5f3066d529cb99
message: source proposal movements pending human confirmation 2026-05-29
```

Contains:

- deletion of `source_proposals/accepted/test3.md`
- deletion of `source_proposals/accepted/test3_copy.md`
- movement of the ALSO PDF from `source_proposals/staging/` to `source_proposals/accepted/`

Why stashed:

Source proposal movement is a real business-data operation. It should not be committed or discarded by an automated model without human confirmation.

How to inspect:

```bash
git stash show --stat --include-untracked db08a940afa00ec5adefd4fece5f3066d529cb99
```

How to restore if approved:

```bash
git stash apply db08a940afa00ec5adefd4fece5f3066d529cb99
```

### 2. Generated Outputs

```text
stash hash: 2fccf98d378ea056fa9a17bc0c21c5a928aab3a4
message: generated outputs before cleanup 2026-05-29
```

Contains generated or derived outputs under:

- `compiled/`
- `reports/`
- `skills/draft/`
- `skills/published/`
- `creative_dna/`
- `skills/v2/`

Why stashed:

These files are produced by pipelines or skill generation. They should not be mixed with source changes. In particular, `skills/published/` and registry-like assets must only change during an explicit publish/release task.

How to inspect:

```bash
git stash show --stat --include-untracked 2fccf98d378ea056fa9a17bc0c21c5a928aab3a4
```

How to restore selectively:

```bash
git checkout 2fccf98d378ea056fa9a17bc0c21c5a928aab3a4 -- path/to/file
```

Do not apply the full stash unless the task is explicitly to review generated outputs.

### 3. Unreviewed Helper Scripts

```text
stash hash: a2f4f9811e70880b5fd17bd5fb5938a87922b473
message: unreviewed helper scripts before cleanup 2026-05-29
```

Contains:

- `scripts/daily_review.sh`
- `skill_builder/scripts/skill_feedback_analysis.py`
- `skill_builder/scripts/validate_skill_output.py`

Why stashed:

These scripts may be useful, but they were not part of the current Node 5/6 task and have not been reviewed for project fit, dependency assumptions, or maintenance cost.

How to inspect:

```bash
git stash show --stat --include-untracked a2f4f9811e70880b5fd17bd5fb5938a87922b473
```

## Removed Duplicate Stash

One duplicate stash was dropped:

```text
3f221cfcee91e7ec7357a09972b9346f13805cf1
```

Reason:

It duplicated the generated-output stash created during an earlier command retry. Keeping it would make later recovery ambiguous.

## Current Rule For Future Models

Do not use:

```bash
git add .
git add -A
```

Before any future commit, run:

```bash
git status --short
git diff --cached --stat
git diff --cached --check
```

Commit categories separately:

| Category | Commit Policy |
|---|---|
| Source code | commit only with tests |
| Tests | commit with related source code |
| Docs | may commit independently |
| Generated outputs | do not commit unless explicitly requested |
| `skills/published/` | publish/release task only |
| `registry/` | publish/release task only |
| `source_proposals/` | human confirmation required |

## Recommended Next Step

Do not move to Node 7 yet.

Next engineering task should be:

```text
Remove or downgrade OpenClaw's hardcoded hotel-to-luxury-hotel-festival routing.
```

Reason:

The promo-video route now has a stage protocol, but non-video hotel briefs may still overfit the old W hotel skill because of hardcoded brand routing in OpenClaw.
