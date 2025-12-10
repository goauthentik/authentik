import "../Divider.js";

import { Divider } from "../Divider.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const metadata: Meta<Divider> = {
    title: "Elements/<ak-divider>",
    component: "ak-divider",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Divider

Divider is a horizontal rule, an in-page element to separate displayed items.

It has no configurable attributes. It does have a single unnamed slot, which is displayed in-line in
the center of the rule. If the CSS Base in loaded into the parent context, icons defined in the base
can be used here.

## Usage

\`\`\`Typescript
import "#elements/Divider";
\`\`\`

\`\`\`html
<ak-divider></ak-divider>
\`\`\`

With content:

\`\`\`html
<ak-divider><p>Time for bed!</p></ak-divider>
\`\`\`

With an icon:

\`\`\`html
<ak-divider><i class="fa fa-bed"></i></ak-divider>
\`\`\`
`,
            },
        },
    },
};

export default metadata;

const container = (content: TemplateResult) => html`
    <style>
        ak-divider {
            display: inline-block;
            width: 32rem;
            max-width: 32rem;
        }</style
    >${content}
`;

export const DefaultStory: StoryObj = {
    render: () => container(html` <ak-divider> </ak-divider> `),
};

export const DividerWithSlottedContent: StoryObj = {
    render: () => container(html` <ak-divider><p>Time for bed!</p></ak-divider> `),
};

export const DividerWithSlottedIcon: StoryObj = {
    render: () => container(html` <ak-divider><i class="fa fa-bed"></i></ak-divider> `),
};
