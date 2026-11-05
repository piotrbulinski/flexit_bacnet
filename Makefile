build:
	rm -rf ./dist
	python3 -m pip install --upgrade build
	python3 -m build

# Releases are published to PyPI by .github/workflows/release.yml
# (trusted publishing + PEP 740 attestations) when a GitHub release is published.
release:
	@echo "Manual uploads are disabled. Bump the version in pyproject.toml, merge to main,"
	@echo "then publish a GitHub release tagged with that version, e.g.:"
	@echo "  gh release create <version> --generate-notes"
	@exit 1
