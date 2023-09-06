---
title: "Procedural topic"
---

:::info
**How to use this template**: start with the markdown version of the template, either by copying the [`procedural.tmpl.md`](https://github.com/goauthentik/authentik/tree/main/website/developer-docs/docs/templates) file from our GitHub repo or downloading the template file using the following command:

```
wget https://raw.githubusercontent.com/goauthentik/authentik/main/website/developer-docs/docs/templates/procedural.tmpl.md
```

Edit your markdown file as you work, reading this page for the descriptions of each section. You can build out a "stub file" with just headers, then gradually add content to each section. Use screenshots sparingly, only for complex UIs where it is difficult to describe a UI element with words. Refer to our [General Guidelines](../writing-documentation#general-guidelines) for writing tips and authentik-specific rules.
:::

For a procedural topic, use a title that focuses on the task you are writing about. For example, "Add a new Group" or "Edit user profiles". For procedural docs, there should be a verb in the title, and usually the noun (the component or object you are working on). For the title (and all headings) use the infinitive form of the verb (i.e. "add") not the gerund form (i.e. "adding").

In this first section, right after the title, write one or two sentences about the task. Keep it brief; if it goes on too long, then create a separate conceptual topic, in a separate `.md` file. We don't want readers to have to scroll through paragraphs of conceptual info before they get to Step 1.

## Prerequisites (optional section)

In this section, inform the reader of anything they need to do, or have configured or installed, before they start following the procedural instructions below.

## Overview of steps/workflow (optional section)

If the task is quite long or complex, it might be good to add a bullet list of the main steps, or even a diagram of the workflow, just so that the reader can first familairize themselves with the 50,000 meter view before they dive into the detailed steps.

## First several group steps

If the task involves a lot of steps, try to group them into similar steps and have a Head3 or Head4 title for each group.

In this section, help the reader get oriented... where do they need to be (i.e. in the GUI, on a CLI, etc).

Have a separate paragraph for each step.

Start instructions with the desired goal, followed by the instructions. For example, in this sentence we first read the goal (to define a new port) and then we see the instructions: "To define a new port number, navigate to the Admin interface, and then to the **Settings** tab."

## Next step of grouped steps (if a second group is needed)

Continue with the steps...

Use screenshots sparingly, only for complex UIs where it is difficult to describe a UI element with words.

Provide as many code snippets and examples as needed.

## Verify the steps

Use a heading such as "Verify your installation" or "Verify successful configuration". Whenever possible, it is useful to add verification steps at the end of a procedural topic. For example, if the procedural was about installing a product, use this section to tell them how they can verify that the install was successful.
