# The Merge-Revert Incident — 2026-05-18

A personal post-mortem and learning note. Keep this around — the next time someone on your team reverts a merge commit and things look weird, this file will save them hours.

> **TL;DR** — Reverting a merge commit with `git revert -m 1 <merge>` silently wipes the *file contents* introduced by that merge, even though all the merged commits still appear in `git log`. The fix is a revert-of-revert on top of current `HEAD`. Direct pushes to `main` and reverts of merge commits are the two operations that turned a small mistake into 30 minutes of detective work.

---

## Table of contents

1. [What I did wrong](#1-what-i-did-wrong)
2. [Why the revert was a disaster, not a fix](#2-why-the-revert-was-a-disaster-not-a-fix)
3. [The mental model: merges add a *set of changes*, not "one commit"](#3-the-mental-model-merges-add-a-set-of-changes-not-one-commit)
4. [Why it was invisible](#4-why-it-was-invisible)
5. [How we diagnosed it](#5-how-we-diagnosed-it)
6. [How we fixed it: revert-of-revert](#6-how-we-fixed-it-revert-of-revert)
7. [The one conflict and the latent bug it exposed](#7-the-one-conflict-and-the-latent-bug-it-exposed)
8. [Cheat sheet for next time](#8-cheat-sheet-for-next-time)
9. [Guardrails to set up so this can't happen again](#9-guardrails-to-set-up-so-this-cant-happen-again)
10. [Glossary](#10-glossary)

---

## 1. What I did wrong

The actual mistake was small and reversible:

```
1. On my branch I committed   5ae5d55  "changes for version"
2. I ran   git merge origin/main   to bring upstream changes in
   → created merge commit  66412d3
3. I typed   git push origin main   (intended to push to my branch)
   → added 5ae5d55 + 66412d3 to public main
```

At this point, public `main` looked like:

```
f62913c  ← main was here before my push  (tip of all PRs #16–#23)
   │
   ├─ 5ae5d55  "changes for version"          (my commit)
   │
   └─ 66412d3  Merge branch 'main' of …       (the merge)
```

Both new commits were *additions on top* — nobody had been working on the broken state yet, so this was recoverable by either:
- A clean `git revert 66412d3 5ae5d55` of just my additions, OR
- Force-push to `main` to `f62913c` (only safe if no one had pulled yet).

## 2. Why the revert was a disaster, not a fix

To clean up, the AI ran:

```bash
git revert -m 1 66412d3      # → produced 160c1fe   ← THE CULPRIT
git revert 5ae5d55           # → produced b762081
```

The second one is fine — it just undoes my own commit.

The first one is the trap. `-m 1` says "treat parent 1 as the mainline I want to keep". For merge commit `66412d3`:

- **Parent 1** = my branch tip (just `5ae5d55`)
- **Parent 2** = origin/main (containing PRs #16–#23 — murli/user-role + dev/role work)

So `git revert -m 1 66412d3` told Git: *"Keep parent 1's state. Undo everything parent 2 brought in."*

That second sentence is the killer. Parent 2 brought in **all the file contents from PRs #16–#23** — `AssignRoleToUserPreLogic.java`, `CreateUsersToRolePreLogic.java`, `RoleService.java`, `UserService.java`, `Role.json`, `openapi.json`, and 7 others. **The revert wiped all of those file contents from the working tree**, while leaving the commits in history.

## 3. The mental model: merges add a *set of changes*, not "one commit"

This is the part to internalize:

> A merge commit doesn't introduce "its own" changes. It introduces **every change from one parent that wasn't already in the other**.

When you revert a normal commit, you undo one commit's diff. When you revert a merge commit, **you undo every change from the non-mainline side of the merge** — which can be dozens of commits from multiple people.

Visualized:

```
      main:    A ── B ── C ── D
                              │
              feature:        ├── E ── F ── G
                                          │
                              merged:     M  ← merge of D and G
```

`git revert -m 1 M` means: *"keep what came from D's side, undo E, F, and G's contents."* Even though E, F, G still appear in `git log`, their file changes are gone from the tree.

The Git docs are blunt about this. From `git-merge(1)`:

> Reverting a merge commit declares that you will never want the tree changes brought in by the merge. As a result, later merges will only bring in tree changes introduced by commits that are not ancestors of the previously reverted merge.

In plain English: once you `revert -m 1` a merge, those changes are *marked as undesired*. Future merges from the same branch won't bring them back unless you explicitly re-merge or cherry-pick them.

## 4. Why it was invisible

After the revert:

- `git log --oneline` on `main` looked **completely normal**. All the PR merges (#16–#23) were still there as ancestors.
- The repo built and pushed fine.
- Other devs merged PRs #24, #25, #27 on top — *on the broken tree*.

The only way to see the problem was a file-level diff against the pre-disaster state. Nothing in the commit log said "by the way, 150 lines across 13 files are missing now."

## 5. How we diagnosed it

One command pinned the whole thing:

```bash
git diff f62913c..origin/main --stat
```

Where `f62913c` was the tip of main *just before* the bad push.

Output showed 13 files differing by ~150 lines — and the list of files matched exactly what `git show --stat 160c1fe` had "reverted":

```
.../assignRoleToUser/AssignRoleToUserPreLogic.java | 12 ++--
.../assignUserToRole/AssignUserToRolePreLogic.java | 10 +--
.../CreateUsersToRolePreLogic.java                 | 50 ++++---------
…
src/main/resources/specs/Role.json                 | 80 +++++++++++++++---
src/main/resources/specs/User.json                 | 20 +++---
src/main/resources/specs/openapi.json              | 18 +----
13 files changed, 145 insertions(+), 152 deletions(-)
```

Same files, same line counts → `160c1fe` was the smoking gun.

**Lesson:** when something on `main` feels off but the log looks clean, compare trees, not commits.

```bash
# pick the commit you believe was "the last good state"
git diff <last-good-sha>..origin/main --stat
```

If files appear there that you didn't expect, someone (or something) edited the tree in a way the log isn't explaining.

## 6. How we fixed it: revert-of-revert

The fix used the same blunt instrument that broke things — a `git revert`, applied to the broken commit:

```bash
# 1. Worktree so my in-progress work on another branch isn't disturbed
git worktree add ../bsquare-codegen-recover origin/main -b recover/main

# 2. Revert the bad revert
cd ../bsquare-codegen-recover
git revert --no-edit 160c1fe          # → 1 conflict, see §7
# (resolve the conflict, git add, then:)
git revert --continue --no-edit       # → 907f873

# 3. Sanity check vs the pre-disaster state
git diff f62913c..HEAD --stat
# → only the legitimate post-disaster PR additions remain
#   (4 lines in User.json from PR #24, the kept rdd join)

# 4. Verify it compiles
mvn -DskipTests compile               # BUILD SUCCESS

# 5. Push the recovery branch, open a PR
git push -u origin recover/main
```

### Why does revert-of-revert work?

A revert generates an **inverse patch** of the commit it targets.
- `160c1fe` = inverse of `(merge − parent1)` = "remove everything PRs #16–#23 added"
- `git revert 160c1fe` = inverse of *that* = re-adds everything PRs #16–#23 added

Crucially, this **only inverts `160c1fe`'s diff**. `b762081` (the revert of my "version changes") is left in place, so the JWT/security bits I deliberately wanted gone *stay gone*.

### Why a worktree?

`git worktree add` creates a second checked-out copy of the repo pointing at a different branch, in a different directory. Benefits:

- My in-progress work on `opt-lock/ayush` (uncommitted changes, untracked files) was untouched.
- No risk of accidentally staging recovery changes into the wrong branch.
- Easy cleanup: `git worktree remove <path>` when done.

This is the right tool any time you need to do work on a different branch without disturbing your current one.

## 7. The one conflict and the latent bug it exposed

`git revert 160c1fe` produced one conflict in `UmtUserQueryRepository.java` — in the `GET_ROLES_BY_USER_ID_SQL` query, around the JOIN clauses.

- **Current main** (after PRs #25/#27) had a `LEFT JOIN reference_data_detail rdd` for the `default_home_label` CASE WHEN expression.
- **Revert target** (restoring murli's work) had a `LEFT JOIN UMT_ROLE r` for the `r.name AS role_name` column in the SELECT.

Resolution: **keep both joins**. The SELECT clause on current main was *already* referencing `r.name AS role_name` even though the `UMT_ROLE r` join was missing — a latent SQL bug that would have blown up at runtime. The fix accidentally closed that hole too.

**Lesson:** in a conflict, before picking a side, **read the surrounding code** — both versions may have been working in isolation but neither is correct in combination.

## 8. Cheat sheet for next time

### When you've accidentally pushed to a shared branch

| Situation | Right move |
|---|---|
| Nobody has pulled yet, branch protection off | `git push --force-with-lease origin <branch>` to the previous good SHA. Communicate. |
| Anyone might have pulled | **Don't force-push.** `git revert <bad-sha>` and push the revert as a new commit. Open a PR. |
| The thing to undo is a merge commit | **STOP.** Read the next section before running `git revert -m 1`. |

### When you must revert a merge commit

1. **Pause.** This is the most foot-gun-y operation in Git. Most engineers do this wrong at least once.
2. Read [`git-merge(1)` "How to revert a faulty merge"](https://git-scm.com/docs/git-merge#_how_to_revert_a_faulty_merge). The whole section. Twice.
3. Consider alternatives **first**:
   - **Revert the individual problem commits**, not the merge. If only `5ae5d55` was bad, revert just `5ae5d55`, not the whole merge.
   - **Move the branch pointer** (if the push is fresh and you can coordinate force-push).
4. If you really must `revert -m 1`, **document it in the commit message** and remember: those changes are now "marked as undesired" — future merges of that branch won't bring them back automatically.
5. After the revert, run `git diff <pre-revert-sha>..HEAD --stat` and confirm the file list matches what you intended to undo. If anything unexpected appears, abort.

### When something on `main` looks wrong but `git log` looks fine

```bash
# Compare tree state, not commits
git diff <last-known-good-sha>..origin/main --stat
git diff <last-known-good-sha>..origin/main -- <suspicious-file>
```

### Useful incident-recovery one-liners

```bash
# Show a merge commit's two parents and what each side brought in
git log --first-parent <merge>^..<merge>
git log <merge>^1..<merge>^2

# What did a commit actually change?
git show --stat <sha>
git show <sha> -- path/to/file

# Find commits that touched a file in a range
git log --oneline <since>..<until> -- path/to/file
```

## 9. Guardrails to set up so this can't happen again

### On GitHub (the highest-leverage one)

Enable **branch protection** on `main`:
- Require pull requests before merging.
- Require at least 1 approval.
- Restrict who can push directly (or block direct pushes entirely).

This single setting would have prevented the original incident outright. Worth 5 minutes of setup.

### On your machine

A pre-push hook that refuses direct pushes to `main`. Drop this in `.git/hooks/pre-push` and `chmod +x` it:

```bash
#!/bin/sh
protected_branch='main'
while read local_ref local_sha remote_ref remote_sha; do
  if [ "$remote_ref" = "refs/heads/$protected_branch" ]; then
    # Check if pushing from a branch other than main
    current_branch=$(git symbolic-ref --short HEAD 2>/dev/null)
    if [ "$current_branch" != "$protected_branch" ]; then
      echo "Direct push to $protected_branch blocked. Open a PR instead."
      exit 1
    fi
    echo "Confirm direct push to $protected_branch? (type 'yes' to continue)"
    read confirm < /dev/tty
    [ "$confirm" = "yes" ] || { echo "Aborted."; exit 1; }
  fi
done
exit 0
```

### When working with AI on git

For any git operation that touches shared history (`revert`, `rebase`, `reset`, `push --force`, anything involving `main`):

- Ask the AI to **explain the plan first**, then run it.
- Have it print the diff/state it expects *before* and *after*, and verify after.
- Treat `git revert -m 1 <merge>` as a "pause and review" trigger, the same way `rm -rf` is.

## 10. Glossary

- **Merge commit** — A commit with two (or more) parents, created by `git merge`. Contains the resolution of combining two histories.
- **`-m N` flag on revert** — When reverting a merge, tells Git which parent is the "mainline" to keep. `-m 1` keeps parent 1, undoes what parent 2 brought.
- **Revert** — Creates a *new* commit that applies the inverse patch of a target commit. Does not rewrite history. Safe on shared branches.
- **Reset** — Moves the branch pointer (and optionally the index/working tree). *Rewrites history if pushed.* Dangerous on shared branches.
- **Force-push** — `git push --force` (or `--force-with-lease`). Overwrites the remote branch's history. Only safe when no one else has based work on the overwritten commits.
- **Worktree** — A second checked-out copy of a repo pointing at a different branch. Created with `git worktree add`. Lets you work on multiple branches in parallel without stashing.
- **Cherry-pick** — Apply a single commit's diff onto your current branch as a new commit. Useful for "I want this one specific change from another branch."

---

## Closing thought

Reverting a merge commit is one of three or four operations in Git that the documentation specifically warns about. The fact that it tripped you up isn't a sign you don't understand Git — it's a sign you encountered the *exact thing* the Git maintainers wrote a whole documentation section warning about.

The diagnosis muscle — *"the log looks fine but a tree-diff shows missing content; what commit could have done that?"* — is the real skill worth keeping from today. Once you've seen the pattern, you'll spot it instantly next time.

Next time someone on the team panics about this, you'll be the one walking them through it.
