import "../Expand.js";

import { Expand, type IExpand } from "../Expand.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const metadata: Meta<Expand> = {
    title: "Elements/<ak-expand>",
    component: "ak-expand",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Expand

Expand is an in-page element used to hide cluttering details that a user may wish to reveal, such as raw
details of an alert or event.

It has one unnamed slot for the content to be displayed.

## Usage

\`\`\`Typescript
import "#elements/Expand";
\`\`\`

\`\`\`html
<ak-expand><p>Your primary content goes here</p></ak-expand>
\`\`\`

To show the expanded content on initial render:

\`\`\`html
<ak-expand expanded><p>Your primary content goes here</p></ak-expand>
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
            ak-divider {
                display: inline-block;
                width: 32rem;
                max-width: 32rem;
            }</style
        >${content}
    </div>`;

export const DefaultStory: StoryObj = {
    args: {
        expanded: false,
        textOpen: undefined,
        textClosed: undefined,
    },

    render: ({ expanded, textOpen, textClosed }: IExpand) =>
        container(
            html` <ak-expand
                ?expanded=${expanded}
                textOpen=${ifDefined(textOpen)}
                textClosed=${ifDefined(textClosed)}
                ><div>
                    <p>Μήτ᾽ ἔμοι μέλι μήτε μέλισσα</p>
                    <p>"Neither the bee nor the honey for me." - Sappho, 600 BC</p>
                </div>
            </ak-expand>`,
        ),
};
export const Expanded = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ expanded: true } },
};
