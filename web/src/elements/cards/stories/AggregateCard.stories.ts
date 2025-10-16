import "../AggregateCard.js";

import { AggregateCard, type IAggregateCard } from "../AggregateCard.js";

import { ifPresent } from "#elements/utils/attributes";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const metadata: Meta<AggregateCard> = {
    title: "Elements/<ak-aggregate-card>",
    component: "ak-aggregate-card",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Aggregate Cards

Aggregate Cards are in-page elements to display isolated elements in a consistent, card-like format.
Cards are used in dashboards and as asides for specific information.

## Usage

\`\`\`Typescript
import "#elements/cards/AggregateCard";
\`\`\`

\`\`\`html
<ak-aggregate-card header="Some title"><p>This is the content of your card!</p></ak-aggregate-card>
\`\`\`
`,
            },
        },
    },
    argTypes: {
        icon: { control: "text" },
        label: { control: "text" },
        headerLink: { control: "text" },
        subtext: { control: "text" },
    },
};

export default metadata;

export const DefaultStory: StoryObj = {
    args: {
        icon: null,
        label: "Default",
        headerLink: null,
        subtext: null,
    },
    render: ({ icon, label, headerLink, subtext }: IAggregateCard) => {
        return html`
            <style>
                ak-aggregate-card {
                    display: inline-block;
                    width: 32rem;
                    max-width: 32rem;
                }
            </style>
            <ak-aggregate-card
                label=${ifPresent(label)}
                headerLink=${ifPresent(headerLink)}
                subtext=${ifPresent(subtext)}
                icon=${ifPresent(icon)}
            >
                <p>
                    Form without content style without meaning quick-win, for that is a good problem
                    to have, so this is our north star design. Can you champion this cross sabers
                    run it up the flagpole, ping the boss and circle back race without a finish line
                    in an ideal world. Price point innovation is hot right now, nor it's not hard
                    guys, but race without a finish line, nor thought shower.
                </p>
            </ak-aggregate-card>
        `;
    },
};
