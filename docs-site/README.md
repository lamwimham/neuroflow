# NeuroFlow Documentation Site

This directory contains the NeuroFlow project documentation website built with [MkDocs](https://www.mkdocs.org/) and the [Material theme](https://squidfunk.github.io/mkdocs-material/).

## Quick Start

### 1. Install Dependencies

```bash
pip install mkdocs mkdocs-material mkdocs-minify-plugin mike
```

Or use the provided script:

```bash
./build.sh
```

### 2. Preview Locally

```bash
mkdocs serve
```

Open http://localhost:8000 in your browser.

### 3. Build

```bash
mkdocs build
```

The built site will be in the `site/` directory.

### 4. Deploy

```bash
# Deploy to GitHub Pages
mike deploy --push main
```

## Documentation Structure

```
docs/
├── index.md                      # Homepage
├── getting-started/              # Quick start guides
│   ├── installation.md
│   ├── quickstart.md
│   └── first-agent.md
├── concepts/                     # Core concepts
│   ├── architecture.md
│   ├── agents.md
│   ├── tools.md
│   └── sandbox.md
├── guides/                       # How-to guides
│   ├── building-agents.md
│   ├── developing-tools.md
│   ├── using-mcp.md
│   ├── debugging.md
│   └── testing.md
├── api-reference/                # API documentation
│   ├── python/
│   │   └── index.md
│   └── rust/
│       └── index.md
├── best-practices/               # Best practices
│   ├── agent-design.md
│   └── performance.md
├── troubleshooting/              # Troubleshooting
│   └── faq.md
└── examples/                     # Code examples
    └── basic.md
```

## Writing Documentation

### Markdown Extensions

This site uses the following Markdown extensions:

- **Admonitions**: Notes, warnings, tips
- **Code highlighting**: Syntax highlighting for code blocks
- **Tables**: Data tables
- **Lists**: Ordered and unordered lists
- **Links**: Internal and external links

### Admonitions

```markdown
!!! note "Note Title"
    This is a note

!!! tip "Tip Title"
    This is a tip

!!! warning "Warning Title"
    This is a warning

!!! info "Info Title"
    This is information
```

### Code Blocks

````markdown
```python
from neuroflow import NeuroFlowSDK

sdk = await NeuroFlowSDK.create()
```
````

### Internal Links

```markdown
[Installation Guide](getting-started/installation.md)
[Architecture Overview](concepts/architecture.md)
```

## Configuration

Edit `mkdocs.yml` to:

- Change site title and description
- Update navigation
- Configure theme options
- Add plugins

## Development

### Adding New Pages

1. Create the Markdown file in the appropriate directory
2. Add the page to the `nav` section in `mkdocs.yml`
3. Test locally with `mkdocs serve`

### Updating Navigation

Edit the `nav` section in `mkdocs.yml`:

```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quick Start: getting-started/quickstart.md
```

### Adding Code Examples

1. Keep examples concise and focused
2. Include comments for complex parts
3. Show both basic and advanced usage
4. Include expected output when helpful

## Build Scripts

### build.sh

Build the documentation:

```bash
./build.sh
```

Preview with live reload:

```bash
./build.sh --serve
```

### deploy.sh

Deploy to GitHub Pages:

```bash
./deploy.sh
```

## Versioning

Documentation versions are managed with `mike`:

```bash
# Deploy new version
mike deploy --push v0.3.0

# Set default version
mike set-default --push main

# List versions
mike list
```

## Troubleshooting

### Build Errors

**Error: Template not found**
- Check that the file path is correct
- Verify the file exists in the `docs/` directory

**Error: Markdown extension not found**
- Install required extensions: `pip install mkdocs-material`

### Preview Issues

**Server not starting**
- Check if port 8000 is in use
- Try a different port: `mkdocs serve --dev-addr localhost:8001`

## Contributing

When contributing to documentation:

1. **Follow the style guide**
   - Use clear, concise language
   - Include code examples
   - Add appropriate admonitions

2. **Test locally**
   - Preview changes with `mkdocs serve`
   - Check all links work
   - Verify code examples run correctly

3. **Update navigation**
   - Add new pages to `mkdocs.yml`
   - Organize related content together

4. **Build and verify**
   - Run `mkdocs build`
   - Check generated HTML in `site/` directory

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/user-guide/)
- [Material Theme Documentation](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
- [Mike Versioning](https://github.com/jimporter/mike)

## License

MIT License - Same as the main NeuroFlow project

---

**NeuroFlow** - Make AI Agent development simpler, safer, and more efficient.
