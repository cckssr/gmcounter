# GitHub Maintenance Workflows

This folder is arranged so the workflows can be copied to another Python pip project with only a few configuration changes.

## What each workflow does

- `ci.yml`: format, lint, and test the package across a Python matrix
- `auto-release.yml`: on merged PRs with a release label (`major`/`minor`/`patch`), bump version, create tag, build distribution, and publish release
- `sphinx-docs.yml`: build and deploy Sphinx documentation to GitHub Pages

## Values to adapt in a new project

- `PROJECT_NAME`
- `CLI_COMMAND`
- `MODULE_COMMAND`
- `REPOSITORY_URL`
- `VERSION_FILES`
- `LINT_DIRS`
- `TEST_COV`
- `INSTALL_EXTRAS`
- `DOCS_DIR`
- `DOCS_REQUIREMENTS`
- `PROJECT_REQUIREMENTS`

## Notes

- `pyproject.toml` is treated as the source of truth for the package version.
- The version workflows update `gmcounter/__init__.py` because the package exposes `__version__` there.
- The automatic PR flow requires one release label on merged PRs: `major`, `minor`, `patch` (or `semver:*`).
- The removed `version-sync-release.yml`, `mdbook.yml`, `pr-label-release.yml`, `version-bump.yml`, `release.yml`, and duplicate `version-sync-release copy.yml` were not aligned with this Python package setup.
