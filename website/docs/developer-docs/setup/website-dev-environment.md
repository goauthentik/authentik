---
title: Documentation development environment
sidebar_label: Docs development
tags:
    - development
    - contributor
    - docs
    - docusaurus
---

This guide covers how to set up your environment for contributing to authentik's documentation.

## Prerequisites

- **Node.js**: Version 24.x recommended (earlier versions may work)
- **Make**: Any recent version

### Installing Node.js

#### Using Homebrew (macOS)

If you use [Homebrew](https://brew.sh/):

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js 24
brew install node@24

# Add to your PATH if needed
echo 'export PATH="/opt/homebrew/opt/node@24/bin:$PATH"' >> ~/.zshrc
```

#### Using nvm (Node Version Manager)

[nvm](https://github.com/nvm-sh/nvm) lets you manage multiple Node.js versions:

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Reload shell configuration
source ~/.bash_profile

# Install and use Node.js 24
nvm install 24
nvm use 24
```

## Setup instructions

1. Clone the repository:

    ```bash
    git clone https://github.com/goauthentik/authentik && cd authentik
    ```

2. Install dependencies:
    ```bash
    make website-install
    ```

## Development workflow

For a complete list of useful commands and detailed documentation workflows, see the [Writing Documentation](../docs/writing-documentation.md#useful-commands) guide.

## Project structure

The documentation is organized as follows:

```
website/
├── docs/                  # Main documentation content
│   ├── installation/      # Installation guides
│   ├── user-guide/        # User guides
│   ├── developer-docs/    # Developer documentation
│   └── ...
├── integrations/          # Integrations documentation
│   ├── services/          # Service-specific integration guides
│   └── template/          # Templates for new integration docs
├── src/                   # Website source code
└── static/                # Static assets (images, etc.)
```

## Additional resources

- [Docusaurus documentation](https://docusaurus.io/docs)
- [Markdown guide](https://www.markdownguide.org/)
- [authentik style guide](../docs/style-guide.mdx)
- [Documentation templates](../docs/templates/index.md)

## Getting help

If you encounter issues not covered in this guide, please reach out through:

- [Discord community](https://goauthentik.io/discord)
- [GitHub issues](https://github.com/goauthentik/authentik/issues)
