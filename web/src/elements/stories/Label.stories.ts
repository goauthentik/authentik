import "../Label.js";

import { type ILabel, Label, PFColor } from "../Label.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

type ILabelForTesting = ILabel & { message: string };

const metadata: Meta<Label> = {
    title: "Elements/<ak-label>",
    component: "ak-label",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Labels

Labels are in-page elements that provide pointers or guidance. Frequently called "chips" in other
design systems. Labels are used alongside other elements to warn users of conditions or status that
they might want to be aware of

## Usage

\`\`\`Typescript
import "#elements/Label";
\`\`\`

Note that the content of a label _must_ be a valid HTML component; plain text does not work here. The
default label is informational:

\`\`\`html
<ak-label><p>This is the content of your label!</p></ak-label>
\`\`\`
`,
            },
        },
    },
    argTypes: {
        compact: { control: "boolean" },
        color: { control: "text" },
        icon: { control: "text" },
        // @ts-ignore
        message: { control: "text" },
    },
};

export default metadata;

export const DefaultStory: StoryObj = {
    args: {
        compact: false,
        message: "Eat at Joe's.",
    },

    // @ts-ignore
    render: ({ compact, color, icon, message }: ILabelForTesting) => {
        return html`
            <style>
                ak-label {
                    display: inline-block;
                    width: 48rem;
                    max-width: 48rem;
                }
            </style>
            <ak-label color=${ifDefined(color)} ?compact=${compact} icon=${ifDefined(icon)}>
                <p>${message}</p>
            </ak-label>
        `;
    },
};

export const SuccessLabel = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{
            color: PFColor.Green,
            message: html`I'll show them! I'll show them <i>all</i>&nbsp;! Mwahahahahaha!`,
        },
    },
};

export const CompactWarningLabel = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{
            compact: true,
            color: "warning",
            icon: "fa-coffee",
            message: "It is time for coffee.",
        },
    },
};

export const DangerLabel = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{ color: "danger", message: "Grave danger? Is there another kind?" },
    },
};
