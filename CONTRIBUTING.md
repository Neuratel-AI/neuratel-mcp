# Contributing to Neuratel SDKs

First off, thank you for considering a contribution! We welcome bug fixes, documentation improvements, and new features that align with the Neuratel API.

## ⚠️ Generated Code Notice

This SDK contains auto-generated type definitions and client code derived from the Neuratel OpenAPI specification. **Do not hand-edit generated files** — they are overwritten on the next codegen run. Generated files are located at:

- **Python**: `src/neuratelai/types/_generated.py`
- **Node**: `src/types/_generated.ts`

If you need a change to generated types, update the upstream OpenAPI spec instead and regenerate. See the `scripts/` directory for codegen tooling.

## Issues or Pull Requests?

- **Bug reports, feature requests, questions** → Open an [issue](../../issues/new/choose)
- **Code changes** → Open a [pull request](../../compare)

## Development Environment

### Python SDK (`neuratel-python`)

```bash
git clone https://github.com/Neuratel-AI/neuratel-python.git
cd neuratel-python
uv sync
```

### Node SDK (`neuratel-node`)

```bash
git clone https://github.com/Neuratel-AI/neuratel-node.git
cd neuratel-node
npm install
```

### MCP Server (`neuratel-mcp`)

```bash
git clone https://github.com/Neuratel-AI/neuratel-mcp.git
cd neuratel-mcp
uv sync
```

## Running Tests

### Python

```bash
uv run pytest
uv run ruff check src/    # linting
```

### Node

```bash
npm test
npx tsc --noEmit          # type checking
```

### MCP

```bash
uv run pytest
uv run ruff check src/    # linting
```

## Code Style

- **Python**: We use [Ruff](https://docs.astral.sh/ruff/) (line-length 100, rules: E, F, I, UP). Format before committing.
- **TypeScript**: We use [Biome](https://biomejs.dev/) for linting and formatting.
- **MCP (Python)**: Same as Python SDK — Ruff, identical config.

## Pull Request Process

1. **Fork** the repository and create a branch from `main`
2. **Write tests** for any new functionality or bug fixes
3. **Run the full test suite** locally before pushing
4. **Open a PR** against `main` with a clear description of the change and motivation
5. **Wait for CI** — all checks must pass before merge
6. **One approval** is required from a maintainer

### PR Title Convention

Use conventional commit prefixes:

- `fix:` — bug fixes
- `feat:` — new features or resources
- `docs:` — documentation only
- `refactor:` — code restructuring with no behavior change
- `chore:` — maintenance, CI, dependency updates

## Releases & Versioning

We follow [Semantic Versioning](https://semver.org/):

- **Patch** (`0.2.x`): Bug fixes, backwards-compatible
- **Minor** (`0.x.0`): New resources or methods, backwards-compatible
- **Major** (`x.0.0`): Breaking API changes

Releases are tagged and published automatically via CI on tag push (`v*`).

## Need Help?

- 📧 Email: dev@neuratel.ai
- 🐛 Bugs: [Open an issue](../../issues/new/choose)
- 💬 General questions: [GitHub Discussions](../../discussions) (if enabled)

## Security Vulnerabilities

See [SECURITY.md](./SECURITY.md) for responsible disclosure instructions. **Do not report security issues via public GitHub issues.**
