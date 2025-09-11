import "../AggregateCard.js";

import { AggregateCard, type IAggregateCard } from "../AggregateCard.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

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
        header: { control: "text" },
        headerLink: { control: "text" },
        subtext: { control: "text" },
        leftJustified: { control: "boolean" },
    },
};

export default metadata;

export const DefaultStory: StoryObj = {
    args: {
        icon: undefined,
        header: "Default",
        headerLink: undefined,
        subtext: undefined,
        leftJustified: false,
    },
    render: ({ icon, header, headerLink, subtext, leftJustified }: IAggregateCard) => {
        return html`
            <style>
                ak-aggregate-card {
                    display: inline-block;
                    width: 32rem;
                    max-width: 32rem;
                }
            </style>
            <ak-aggregate-card
                header=${ifDefined(header)}
                headerLink=${ifDefined(headerLink)}
                subtext=${ifDefined(subtext)}
                icon=${ifDefined(icon)}
                ?left-justified=${leftJustified}
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
