# GitHub Maintenance Workflows

This folder is arranged so the workflows can be copied to another Python pip project with only a few configuration changes.

## What each workflow does

- `ci.yml`: format, lint, and test the package across a Python matrix
- `release.yml`: build distribution artifacts and publish a GitHub release from a tag
- `version-bump.yml`: manually bump the package version, commit it, create a tag, and publish the release directly
- `sphinx-docs.yml`: build and deploy Sphinx documentation to GitHub Pages

## Values to adapt in a new project

- `PROJECT_NAME`
- `CLI_COMMAND`
- `MODULE_COMMAND`
- `REPOSITORY_URL`
- `LINT_DIRS`
- `TEST_COV`
- `INSTALL_EXTRAS`
- `DOCS_DIR`
- `DOCS_REQUIREMENTS`
- `PROJECT_REQUIREMENTS`

## Notes

- `pyproject.toml` is treated as the source of truth for the package version.
- The version workflows update `gmcounter/__init__.py` because the package exposes `__version__` there.
- The removed `version-sync-release.yml`, `mdbook.yml`, and duplicate `version-sync-release copy.yml` were not aligned with this Python package setup.