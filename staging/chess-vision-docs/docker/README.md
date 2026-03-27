# Documentation Development Container

## Quick Start

```bash
cd docker
docker-compose up -d docs-dev
```

## Usage

Docs served at `http://localhost:8000` with live reload.

```bash
# Inside container
mkdocs serve --dev-addr=0.0.0.0:8000

# Build
mkdocs build

# Deploy (if configured)
mkdocs gh-deploy
```

## Features

- MkDocs with Material theme
- Mermaid diagrams
- PlantUML support
