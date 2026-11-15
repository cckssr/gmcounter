# GitHub workflows

This file describes the CI and release automation. It is not named `README.md` on purpose: GitHub shows `.github/README.md` on the repository page instead of the project README.

## Overview

| Workflow           | Runs when                                                                            | Does                                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `ci.yml`           | A pull request is opened or updated; manual dispatch; called by the release workflow | `ruff format --check`, `ruff check`, then one pytest run with coverage on Python 3.10, 3.11 and 3.12      |
| `auto-release.yml` | A pull request with a release label is merged into `main`; manual dispatch           | Bumps the version, stamps `CHANGELOG.md`, builds and checks the wheel, tags, publishes the GitHub release |
| `sphinx-docs.yml`  | A push to `main`; manual dispatch                                                    | Builds the Sphinx documentation and deploys it to GitHub Pages                                            |

## Where the tests run

The tests run once per pull request update, and nowhere else:

- There is no `push` trigger in `ci.yml`. A push to a PR branch would run the same tests as the PR itself.
- Merging to `main` does not run them again, and neither does the release. The release only builds the package and checks the wheel (it contains `config.json` and the Designer forms, and no mocks).
- A manual release has no PR behind it, so `auto-release.yml` calls `ci.yml` first.
- New commits on a PR cancel the run they replace.

The merge result is not tested again, so enable branch protection on `main` with "Require branches to be up to date before merging" and "Require status checks to pass" for the CI jobs. Otherwise a PR can pass on an old base and break `main` after the merge.

A direct push to `main` (without a PR) is not tested either. Start `ci.yml` by hand in that case.

## Releasing

1. Describe the change under `## [Unreleased]` in `CHANGELOG.md` (Added, Changed, Fixed, Removed). Write it in the PR that makes the change.
2. Open the PR and wait for CI.
3. Add one label before merging: `major`, `minor` or `patch` (`semver:major` and so on work as well; with several labels the highest wins). A PR without such a label is merged and nothing is released.
4. Merge. The release workflow does the rest: new version in `pyproject.toml`, `gmcounter/__init__.py` and `gmcounter/config.json`, the `Unreleased` section renamed to `[X.Y.Z] - date` with a new empty `Unreleased` above it, a commit `chore: bump version to vX.Y.Z`, the tag `vX.Y.Z`, and the GitHub release with the changelog section as its text and the wheel and sdist attached.

For a pre-release or a release without a PR, start `Auto Release` by hand (Actions → Auto Release → Run workflow) and choose the bump and the pre-release type.

Never edit the version by hand. If a release has no entries under `Unreleased`, the workflow warns and falls back to GitHub's generated notes.

### Secrets

- `PAT_TOKEN` (optional): a personal access token that can push to `main`. Use it when `main` is protected so that the version commit can be pushed. Without it the workflow uses `GITHUB_TOKEN`, whose pushes do not trigger other workflows. With a token the bump commit triggers `sphinx-docs.yml` (a docs rebuild), but not `ci.yml`.

## Adapting the workflows to another project

Change these values:

- `VERSION_FILES` and `CHANGELOG_FILE` in `auto-release.yml`
- the launch lines in the "Compose release notes" step and the assertions in "Check the wheel"
- `LINT_DIRS`, `TEST_COV` and `INSTALL_EXTRAS` in `ci.yml`, plus the system packages that the tests need
- `DOCS_DIR` and `DOCS_REQUIREMENTS` in `sphinx-docs.yml`

`pyproject.toml` is the source of truth for the version.
