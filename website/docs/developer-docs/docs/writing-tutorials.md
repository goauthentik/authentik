---
title: Writing Tutorials
---

# Writing tutorials for authentik

Tutorials are an essential part of authentik's documentation that help users learn by doing. Unlike general documentation that explains concepts and features, tutorials provide step-by-step guidance for accomplishing specific tasks with authentik.

## What makes a good tutorial?

A good authentik tutorial:

1. **Has a clear goal**: Users should know exactly what they'll achieve by following the tutorial.
2. **Is task-oriented**: Focuses on completing a specific task rather than explaining concepts.
3. **Is step-by-step**: Provides clear, sequential instructions that users can follow.
4. **Is practical**: Addresses real-world use cases that users are likely to encounter.
5. **Is self-contained**: Includes all necessary information without requiring users to reference multiple other documents.
6. **Shows results**: Demonstrates what success looks like at each step.
7. **Anticipates challenges**: Addresses common pitfalls and provides troubleshooting guidance.
8. **Is concise**: Respects the user's time by being direct and focused.

## Tutorial vs. Documentation

**todo(dominic): ye nah . for vs and capitalization**

| Tutorial                         | Documentation                                              |
| -------------------------------- | ---------------------------------------------------------- |
| Task-oriented ("How to...")      | Concept-oriented ("What is...")                            |
| Linear, step-by-step format      | Reference format, can be read in any order                 |
| Hands-on, with specific examples | Coverage of features                                       |
| Focused on a single use case     | Covers multiple scenarios                                  |
| Shows the process                | Explains the product                                       |
| Success-oriented                 | Completeness-oriented **todo(dominic): confirm with tana** |

## Choosing tutorial topics

Good candidates for tutorials include:

- **Complex workflows**: Creating multi-factor authentication flows
- **Advanced configurations**: Setting up enterprise features or complex policies
- **Migration paths**: Moving from other identity providers to authentik
- **Problem-solving guides**: Addressing specific challenges users face

When choosing a topic, ask yourself:

- Is this a task many users need to accomplish?
- Does this task require multiple steps that might be confusing?
- Would a step-by-step guide significantly reduce friction?
- Is this something that generates frequent support questions? **todo(dominic): maybe link gh issues/discussions + discord??**

## Tutorial structure

**todo(dominic): might clash with the template?? tbd @tana**

Every authentik tutorial should follow this general structure:

1. **Title**: Clear and action-oriented (e.g., "Setting up GitHub OAuth with authentik")
2. **Overview**: Brief introduction to what the tutorial covers and why it's valuable
3. **What You'll Learn**: Bullet points of specific skills/knowledge gained
4. **Prerequisites**: What users need before starting (versions, permissions, external accounts)
5. **Step-by-Step Instructions**: The main content, broken into clear, numbered steps
6. **Verification**: How to confirm the setup works correctly
7. **Troubleshooting**: Common issues and solutions
8. **Next Steps**: What users might want to do after completing the tutorial

## Writing guidelines

**todo(dominic): Maybe say in a way "style guide + this?**
**todo(dominic): Maybe no "" around do/dont**

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

Use screenshots to clarify complex UI interactions, but don't overuse them as they can become outdated quickly. **todo(dominic): and because it looks weird having like a million screenshots? probably best to say it more diplomatically. TBD**

**todo(dominic): probably covered in style guide**
**Best practices for screenshots**:

- Capture only the relevant portion of the screen
- Use annotations (arrows, highlights) to draw attention to specific elements
- Include screenshots for complex forms or non-obvious UI elements
- Update screenshots when the UI changes significantly

### Provide context

Explain why users are performing each step, not just what they're doing.

**Do**: "Enter your Client ID from GitHub. This unique identifier connects authentik to your specific GitHub application."
**Don't**: "Enter your Client ID from GitHub."

### Use consistent formatting

**todo(dominic): Get rid of this copy paste from the style guide and link it, however i need to find a more central place to link it from first**

Follow these formatting guidelines:

- Use **bold** for UI elements (buttons, fields, tabs)
- Use `code formatting` for values users need to enter or code snippets
- Use numbered lists for sequential steps
- Use bullet points for non-sequential items
- Use admonitions (:::tip, :::warning, :::info) for important notes

### Include Code Examples

When including code or configuration examples:

- Use syntax highlighting
- Provide comments explaining key parts
- Show complete, working examples
- Explain what each part does

```yaml
client_id: <client_id>
client_secret: <client_secret>  todo(dominic): we might want a different way of doing this to be more friendly than procedural/integr
oauth_discovery_url: https://authentik.company/application/o/<application_slug>
```

### Test Your Tutorial

Follow your own instructions from start to finish to ensure they work as expected. Ideally, have someone else test it too.

- Test on a fresh environment if possible
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

**todo(dominic): do we want to impose this burden?**

Tutorials require regular maintenance to stay relevant:

- Update when features change
- Refresh screenshots when the UI changes
- Address common questions in the troubleshooting section
- Add new verification steps as needed

## Need Help?

If you need assistance while writing your tutorial, feel free to:

- Ask questions in our [Discord community](https://goauthentik.io/discord)
- Open an issue on [GitHub](https://github.com/goauthentik/authentik/issues/new?template=documentation.yml)
- Review existing tutorials for inspiration and formatting examples
