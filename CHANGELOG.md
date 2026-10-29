# Changelog

All notable changes to ExoMind.

## [Unreleased] - 2026-02-12
- Added agent-neutral `skills/exomind/SKILL.md` and `scripts/install-agent.sh` so the same MCP server wires into both Pi and Hermes Agent.
- Documented Pi/Hermes integration paths; `pi-context` and `mcp` help text no longer imply Pi-only support.
- Adopted BM25 length normalization, Vietnamese accent folding, relevance-gated graph boosts, and query-local evidence excerpts in native recall.
- Preserved graph cache compatibility with legacy TF-IDF files and documented reindex requirement and semantic-weight flag meaning.
- Added optional local BGE-M3 hybrid retrieval with reciprocal-rank fusion and private benchmark tooling.
- Formalized public-facing documentation, templates, and metadata.
- Added initial changelog entry for tracking future releases.

## [0.9.1-beta.1] - 2026-02-12
- Set pre-release versioning for Rust and Python packages.
- Restricted GitHub release workflow to beta tags only (`v*-beta*`).
- Marked GitHub releases as prerelease by default.
