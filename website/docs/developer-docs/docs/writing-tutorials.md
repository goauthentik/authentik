---
title: Writing tutorials
---

# Writing tutorials for authentik

Tutorials teach by doing. A tutorial should guide a reader through one concrete task, with a clear starting point and a verifiable end state.

## What a tutorial is

A strong tutorial is:

1. **Goal-oriented**: It starts with a clear outcome.
2. **Task-driven**: It focuses on one practical task.
3. **Sequential**: Steps are ordered and easy to follow.
4. **Runnable**: Instructions are specific enough to execute without guesswork.
5. **Verifiable**: It shows how to confirm success.

## Tutorial vs. other doc types

| Type       | Primary purpose                      | Reader behavior                       |
| ---------- | ------------------------------------ | ------------------------------------- |
| Tutorial   | Learn by completing one task         | Follows steps in order                |
| Procedural | Complete an operational task quickly | Skims to relevant step                |
| Conceptual | Understand why and when to use       | Reads for context and decision-making |
| Reference  | Look up exact values/syntax          | Jumps directly to specific details    |

## Choose the right topic

Pick topics that benefit from guided execution:

- Multi-step workflows.
- Error-prone or easy-to-misconfigure setups.
- Frequent onboarding tasks.
- Integrations where verification is important.

Avoid tutorial format for pure background material or lookup tables.

## Use the template

Start with the [tutorial template](./templates/tutorial-template.mdx). The template is frontmatter-first and already includes:

- Learning Center metadata placeholders.
- A recommended section order.
- Admonition usage patterns.
- Verification and troubleshooting structure.

## Writing standards

Follow the [Style Guide](./style-guide.mdx), then apply these tutorial-specific rules.

### Write for execution

- Start each step with an action verb.
- Name exact UI elements, paths, commands, and values.
- Keep each step focused on one action.

### Explain why only when it helps completion

- Add short context when it prevents mistakes.
- Move deep conceptual explanations to a separate conceptual page.

### Keep admonitions intentional

- Use `:::info` for optional context.
- Use `:::warning` for risky actions.
- Use `:::danger` only for irreversible impact.

### Keep code examples runnable

- Prefer minimal, complete snippets.
- Avoid pseudo-config unless clearly labeled.
- Include only fields relevant to the task.

## Quality checklist before opening a PR

1. Follow the tutorial from a clean baseline.
2. Confirm every command and path still works.
3. Verify the expected result section is accurate.
4. Validate links and cross-references.
5. Run local checks from [Writing documentation](./writing-documentation.md).

## Publishing in the Learning Center

If the tutorial is part of the Learning Center, populate `sidebar_custom_props` in frontmatter using the fields from the template.

Canonical Learning Center authoring guidance lives in [Writing documentation: Developing the Learning Center](./writing-documentation.md#developing-the-learning-center).

## Submission and maintenance

1. Submit the PR with the tutorial and required sidebar updates.
2. Address reviewer feedback, especially around clarity and testability.
3. Revisit tutorials when UI, feature behavior, or recommended patterns change.
