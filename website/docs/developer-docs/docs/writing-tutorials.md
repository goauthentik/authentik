---
title: Writing Tutorials
---

# Writing tutorials for authentik

Tutorials are an essential part of authentik's documentation that help users learn by doing. Unlike general documentation that explains concepts and features, tutorials provide step-by-step guidance for accomplishing specific tasks with authentik.

## What makes a good tutorial?

A good authentik tutorial:

1. **Has a clear goal**: users should know exactly what they'll achieve by following the tutorial.
2. **Is task-oriented**: focuses on completing a specific task rather than explaining concepts.
3. **Is step-by-step**: provides clear, sequential instructions that users can follow.
4. **Is practical**: addresses real-world use cases that users are likely to encounter.
5. **Is self-contained**: includes all necessary information without requiring users to reference multiple other documents.
6. **Shows results**: demonstrates what success looks like at each step.
7. **Anticipates challenges**: addresses common pitfalls and provides troubleshooting guidance.
8. **Is concise**: respects the user's time by being direct and focused.

## Tutorial vs. Documentation

| Tutorial                                   | Documentation                                                       |
| ------------------------------------------ | ------------------------------------------------------------------- |
| Very specific tasks, with specific results | Task-oriented, but with more generic steps and room for adjustments |
| Linear, step-by-step format                | Reference format, can be read in any order                          |
| Hands-on, with specific examples           | Coverage of features                                                |
| Focused on a single use case               | Covers multiple scenarios                                           |
| Shows the process                          | Explains the product                                                |
| Success-oriented                           | Completeness-oriented                                               |

## Choosing tutorial topics

Good candidates for tutorials include:

- **Complex workflows**: creating multi-factor authentication flows
- **Advanced configurations**: setting up enterprise features or complex policies
- **Problem-solving guides**: addressing specific challenges users face
- **Frequent or popular tasks**: customizing your icons, or send an email invitation

When choosing a topic, ask yourself:

- Is this a task many users need to accomplish?
- Does this task require multiple steps that might be confusing?
- Would a step-by-step tutorial significantly reduce friction?

## Writing guidelines

In addition to following our [Style Guide](./style-guide.mdx), follow these pointers for creating tutorials.

### Be conversational

Write in a friendly, conversational tone. Use "you" to address the reader directly.

**Do**: "You'll need to configure your application settings before proceeding."
**Don't**: "The application settings should be configured before proceeding."

### Focus on the user's goal

Keep the end goal in mind and make sure every step contributes to that goal.

**Do**: "Click 'Create Provider' to set up the connection that will allow your users to log in."
**Don't**: "Click 'Create Provider' to access the provider creation interface."

### Use clear, action-oriented language

Start steps with verbs (Click, Navigate, Enter, etc.) and be specific about what users need to do.

**Do**: "Click the 'Applications' tab in the left sidebar."
**Don't**: "The Applications tab can be found in the left sidebar."

### Include screenshots

Use screenshots to clarify complex UI interactions, but don't overuse them as they can become outdated quickly. Prefer a small number of focused images to avoid visual clutter, and rely on concise text for straightforward actions. Additional guidance can be found in our [Style Guide](./style-guide.mdx#images-and-media).

### Provide context

Explain **why** users are performing each step, not just what they're doing.

**Do**: "Enter your Client ID from GitHub. This unique identifier connects authentik to your specific GitHub application."
**Don't**: "Enter your Client ID from GitHub."

### Use consistent formatting

Refer to the central [Style Guide: Formatting guidelines](./style-guide.mdx#formatting-guidelines) for conventions on bold text, code formatting, lists, and admonitions. Apply those rules consistently throughout the tutorial.

### Include Code Examples

When including code or configuration examples:

- Use syntax highlighting
- Provide comments explaining key parts
- Show complete, working examples
- Explain what each part does

```yaml
client_id: <client_id>
client_secret: <client_secret>
oauth_discovery_url: https://authentik.company/application/o/<application_slug>
```

### Test Your Tutorial

Follow your own instructions from start to finish to ensure they work as expected. Ideally, have someone else test it too.

- Test on a fresh environment if possible
- Test on the most recent release
- Follow your own steps exactly as written
- Note any points of confusion or ambiguity
- Verify that the end result works as described

## Tutorial Template

We provide a [tutorial template](./templates/tutorial-template.mdx) to help you get started. This template includes all the necessary sections and formatting guidelines.

## Submitting Your Tutorial

When your tutorial is ready:

1. Make sure it follows our [Style Guide](./style-guide.mdx)
2. Run the linting and build checks as described in [Writing Documentation](./writing-documentation.md)
3. Test your tutorial by following it step-by-step
4. Submit a PR to the authentik repository

## Maintaining Tutorials

Tutorials require regular maintenance to stay relevant:

- Update when features change
- Refresh screenshots when the UI changes
- Address common questions in the troubleshooting section
- Add new verification steps as needed
