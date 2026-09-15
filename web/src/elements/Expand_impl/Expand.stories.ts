/**
 * @file Storybook stories for the default Expand component implementation
 */

import "../Expand";

import { type ExpandProps } from "../Expand";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const metadata: Meta<ExpandProps> = {
    title: "Elements/<ak-expand>",
    component: "ak-expand",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Expand

Expand is our Summary/Detail component, used for progressive reveal (of secrets or passwords), or
just as a way to declutter the page.

It has an unnamed slot for the content to be displayed.

## Usage

\`\`\`Typescript
import "#elements/Expand";
\`\`\`

\`\`\`html
<ak-expand><p>Your primary content goes here</p></ak-expand>
\`\`\`
`,
            },
        },
    },
    argTypes: {
        expanded: { control: "boolean" },
        textOpen: { control: "text" },
        textClosed: { control: "text" },
    },
};

export default metadata;

const container = (content: TemplateResult) =>
    html` <div>
        <style>
            ak-expand {
                display: inline-block;
                width: 32rem;
                max-width: 32rem;
            }</style
        >${content}
    </div>`;

type Story = StoryObj<ExpandProps>;

export const DefaultStory: Story = {
    args: {
        expanded: false,
        textOpen: undefined,
        textClosed: undefined,
    },

    render: ({ expanded, textOpen, textClosed }) =>
        container(
            html` <ak-expand
                ?expanded=${expanded}
                text-open=${ifDefined(textOpen)}
                text-closed=${ifDefined(textClosed)}
                ><div>
                    <p>Μήτ᾽ ἔμοι μέλι μήτε μέλισσα</p>
                    <p>"Neither the bee nor the honey for me." - Sappho, 600 BC</p>
                </div>
            </ak-expand>`
        ),
};

export const Expanded: Story = {
    ...DefaultStory,
    args: { ...DefaultStory.args, expanded: true },
};
