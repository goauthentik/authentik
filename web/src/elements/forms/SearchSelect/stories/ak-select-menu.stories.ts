import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj } from "@storybook/web-components";
import { slug } from "github-slugger";

import { TemplateResult, html } from "lit";

import { AkSelectMenu } from "../ak-select-menu.js";
import "../ak-select-menu.js";

const goodForYouRaw = `
Apple, Arrowroot, Artichoke, Arugula, Asparagus, Avocado, Bamboo, Banana, Basil, Beet Root,
Blackberry, Blueberry, Bok Choy, Broccoli, Brussels sprouts, Cabbage, Cantaloupes, Carrot,
Cauliflower, Celery, Chayote, Chives, Cilantro, Coconut, Collard Greens, Corn, Cucumber, Daikon,
Date, Dill, Eggplant, Endive, Fennel, Fig, Garbanzo Bean, Garlic, Ginger, Gourds, Grape, Guava,
Honeydew, Horseradish, Iceberg Lettuce, Jackfruit, Jicama, Kale, Kangkong, Kiwi, Kohlrabi, Leek,
Lentils, Lychee, Macadamia, Mango, Mushroom, Mustard, Nectarine, Okra, Onion, Papaya, Parsley,
Parsley root, Parsnip, Passion Fruit, Peach, Pear, Peas, Peppers, Persimmon, Pimiento, Pineapple,
Plum, Plum, Pomegranate, Potato, Pumpkin, Radicchio, Radish, Raspberry, Rhubarb, Romaine Lettuce,
Rosemary, Rutabaga, Shallot, Soybeans, Spinach, Squash, Strawberries, Sweet potato, Swiss Chard,
Thyme, Tomatillo, Tomato, Turnip, Waterchestnut, Watercress, Watermelon, Yams
`;

const keyToPair = (key: string): DualSelectPair => [slug(key), key];
const goodForYou: DualSelectPair[] = goodForYouRaw
    .split("\n")
    .join(" ")
    .split(",")
    .map((a: string) => a.trim())
    .map(keyToPair);

const selectOne = () => goodForYou[Math.floor(Math.random() * goodForYou.length)][0];

const metadata: Meta<AkSelectMenu> = {
    title: "Elements / Search Select / Menu Items",
    component: "ak-select-menu",
    parameters: {
        docs: {
            description: {
                component: "The actual drop-down for a dynamic menu",
            },
        },
    },
    argTypes: {
        options: {
            type: "string",
            description: "An array of [key, label] pairs of what to show",
        },
        selected: {
            type: "string",
            description: "An array of [key] of what has already been selected",
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) =>
    html` <div style="background: #fff; padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        ${testItem}
        <p>Messages received from the button:</p>
        <ul id="action-button-message-pad" style="margin-top: 1em"></ul>
    </div>`;

type Story = StoryObj;

export const Default: Story = {
    render: () =>
        container(
            html` <ak-select-menu .options=${goodForYou} value=${selectOne()}></ak-select-menu>`,
        ),
};

const goodForYouGroups = (() => {
    const grouped = Object.groupBy(goodForYou, (item) => item[1][0]);
    const keys = Object.keys(grouped);
    keys.sort();
    return keys.map((key) => [`Starts with "${key}"`, grouped[key]]);
})();

export const Grouped: Story = {
    render: () =>
        container(
            html` <ak-select-menu
                .options=${goodForYouGroups}
                value=${selectOne()}
            ></ak-select-menu>`,
        ),
};

const goodForYouDescriptions = goodForYou.map(([key, label]) => [
    key,
    html`<div class="pf-c-dropdown__menu-item-main">${label}</div>
        <div class="pf-c-dropdown__menu-item-description">A description of ${key}</div>`,
]);

export const Descriptive: Story = {
    render: () =>
        container(
            html` <ak-select-menu
                .options=${goodForYouDescriptions}
                value=${selectOne()}
            ></ak-select-menu>`,
        ),
};
