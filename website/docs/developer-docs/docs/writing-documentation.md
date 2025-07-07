---
title: Writing documentation
---

# Writing documentation

This guide explains how to add and edit documentation for authentik. Follow these steps to contribute effectively to our documentation.

## Style guide and writing templates

For writing style, formatting guidelines, and best practices, refer to our [Style Guide](./style-guide.mdx). The style guide covers important aspects like:

- Capitalization and terminology
- Formatting conventions
- Word choices and phrasing
- Document structure
- And more

You can also find templates for different types of documentation in our [Templates section](./templates/index.md).

## Step 1: Set up your environment

For environment setup instructions, see the [Docs Development Environment](../setup/website-dev-environment.md) page. This will guide you through installing the necessary tools.

## Step 2: Understand the documentation commands

Here are the key commands for documentation development:

| Command                   | Description                                        |
| ------------------------- | -------------------------------------------------- |
| `make website-install`    | Install dependencies                               |
| `make website`            | Run linters and formatters (run before committing) |
| `make website-lint-fix`   | Fix formatting issues                              |
| `make website-watch`      | Start main documentation server                    |
| `make integrations-watch` | Start integrations documentation server            |

## Step 3: Create your documentation

### For main documentation

1. **Choose the appropriate section** for your new document based on its content:

    - Installation guides
    - User guides
    - Developer documentation
    - Troubleshooting guides
    - And more...

2. **Create your document** using one of our [templates](./templates/index.md) as a starting point. Use Markdown (`.md`) or MDX (`.mdx`) format:

    ```md
    ---
    title: Your Document Title
    ---

    Content goes here...
    ```

3. **Add to sidebar** by editing the sidebar file in the website directory to ensure your document appears in the table of contents:
    ```javascript
    // In sidebars/docs.mjs
    export default {
        docs: [
            {
                type: "category",
                label: "Category Name",
                items: ["path/to/your-file", "another-file"],
            },
            // other categories...
        ],
    };
    ```

### For integration documentation

1. **Create a new file** in the appropriate services directory:

    - Create a directory for your service if it doesn't exist
    - Use `index.md` for the integration page

2. **Use the template** from the [integrations template](/integrations/template/service.md) as a starting point.

3. **Add to sidebar** by adding your service to the appropriate category in the sidebar file:
    ```javascript
    // In sidebars/integrations.mjs
    {
        type: "category",
        label: "Category Name",
        items: [
            "services/existing-service/index",
            "services/your-service-name/index",  // Add your service here
        ],
    },
    ```

## Step 4: Test your documentation locally

1. Run the development server to preview your changes:

    ```bash
    make website-watch
    ```

    For integration documentation, use:

    ```bash
    make integrations-watch
    ```

2. Open your browser to view the documentation:

    - Main documentation: http://localhost:3000/docs
    - Integrations: http://localhost:3001

3. Verify that your document appears in the navigation and renders correctly.

## Step 5: Submit your changes

1. Before committing, run the linter and formatter:

    ```bash
    make website
    ```

2. Commit your changes and create a pull request with a clear description of what you've added or modified.

3. Respond to reviewer feedback if necessary.

4. Once approved, your documentation will be merged and published! 🎉
