---
title: Writing documentation
---

# Creating documentation

This guide explains how to add and edit documentation for authentik. For environment setup instructions, see the [Docs Development Environment](../setup/website-dev-environment.md) page.

For writing style, formatting guidelines, and best practices, refer to our [Style Guide](./style-guide.mdx).

## Useful commands

Here are the key commands for documentation development:

| Command                   | Description                                        |
| ------------------------- | -------------------------------------------------- |
| `make website-install`    | Install dependencies                               |
| `make website`            | Run linters and formatters (run before committing) |
| `make website-lint-fix`   | Fix formatting issues                              |
| `make website-watch`      | Start main documentation server                    |
| `make integrations-watch` | Start integrations documentation server            |

## Adding main documentation

1. **Choose the appropriate section** for your new document based on its content:

    - Installation guides
    - User guides
    - Developer documentation
    - Troubleshooting guides
    - And more...

2. **Create your document** using Markdown (`.md`) or MDX (`.mdx`) format:

    ```md
    ---
    title: Your Document Title
    ---

    Content goes here...
    ```

3. **Add to sidebar** by editing the sidebar file in the website directory:
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

## Adding integration documentation

1. **Create a new file** in the appropriate services directory:

    - Create a directory for your service if it doesn't exist
    - Use `index.md` for the main integration page
    - For complex integrations with multiple pages, add additional `.md` files in the same directory

2. **Use the template** from the [integrations template](/integrations/template/service.md) as a starting point.

3. **Add to sidebar** by editing the integrations sidebar file:
    ```javascript
    // In sidebars/integrations.mjs
    export default {
        integrations: [
            {
                type: "category",
                label: "Category Name",
                items: ["services/your-service-name/index"],
            },
            // other categories...
        ],
    };
    ```

## Document structure

### Main documentation

For standard documentation, include these elements:

- **Frontmatter** with title and any relevant metadata.
- **Introduction** explaining the purpose of the document.
- **Prerequisites** if applicable.
- **Step-by-step instructions** with clear headings.
- **Examples** where helpful.
- **Related documentation** links.

### Integration documentation

For integration documents, include:

1. **Overview** - Brief description of the integration.
2. **Prerequisites** - Required components and configuration.
3. **authentik Configuration** - Steps to configure authentik.
4. **Service Configuration** - Steps to configure the third-party service.
5. **Testing** - How to verify the integration works.
6. **Troubleshooting** - Common issues and solutions.
7. **References** - Add links to official documentation.

## Using templates

We provide templates to help maintain consistency:

- For main documentation: Check the templates directory under developer docs.
- For integrations: Look for the template file in the integrations directory.

## Document maintenance

- Review existing docs periodically for accuracy.
- Update content when features change.
- Remove documentation for deprecated features.

## Submitting changes

1. Make your changes on a new branch.
2. Run `make website` to ensure proper formatting.
3. Submit a pull request with a clear description.
4. Respond to reviewer feedback.
