import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { AggregateCard, type IAggregateCard } from "../AggregateCard.js";
import "../AggregateCard.js";

const metadata: Meta<AggregateCard> = {
    title: "Elements/<ak-aggregate-card>",
    component: "ak-aggregate-card",
    parameters: {
        docs: {
            description: "A specialized card for displaying collections",
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
        return html` <div style="background-color: #f0f0f0; padding: 1rem;">
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
        </div>`;
    },
};
