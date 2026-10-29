import "#elements/messages/MessageContainer";
import { AkDualSelect } from "../ak-dual-select.js";
import "../ak-dual-select.js";

import { type DualSelectPair } from "../types.js";

import { PageChangeEvent } from "#elements/Paginator";

import { Meta, StoryObj } from "@storybook/web-components";
import { kebabCase } from "change-case";

import { html, LitElement, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

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

const keyToPair = (key: string): DualSelectPair => [kebabCase(key), key, key];

const goodForYou: DualSelectPair[] = goodForYouRaw
    .split("\n")
    .join(" ")
    .split(",")
    .map((a: string) => a.trim())
    .map(keyToPair);

const metadata: Meta<AkDualSelect> = {
    title: "Elements / Dual Select / Dual Select With Pagination",
    component: "ak-dual-select",
    parameters: {
        docs: {
            description: {
                component: "The three-panel assembly",
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
        itemCount: {
            type: "number",
            description: "The number of items in the total collection",
        },
        page: {
            type: "number",
            description: "The current page you're on",
        },
    },
};

export default metadata;

@customElement("ak-sb-fruity")
export class AkSbFruity extends LitElement {
    @property({ type: Array })
    options: DualSelectPair[] = goodForYou;

    @property({ attribute: "page-length", type: Number })
    pageLength = 20;

    @property({ attribute: "item-count", type: Number })
    itemCount = goodForYou.length;

    @property({ attribute: "page", type: Number })
    page = 1;

    constructor() {
        super();
        this.onNavigation = this.onNavigation.bind(this);
        this.addEventListener(PageChangeEvent.eventName, this.onNavigation);
    }

    onNavigation({ page }: PageChangeEvent) {
        if ((page - 1) * this.pageLength > this.options.length) {
            console.warn(
                `Attempted to index from ${page} for options length ${this.options.length}`,
            );

            return;
        }

        this.page = page;
    }

    get pageoptions() {
        return this.options.slice(this.pageLength * (this.page - 1), this.pageLength * this.page);
    }

    render() {
        return html`<ak-dual-select
            .options=${this.pageoptions}
            items-per-page=${this.pageLength}
            item-count=${this.itemCount}
            page=${this.page}
        ></ak-dual-select>`;
    }
}

const container = (testItem: TemplateResult) =>
    html` <div style="padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        <ak-message-container></ak-message-container>
        ${testItem}
        <p>Messages received from the button:</p>
        <div id="action-button-message-pad" style="margin-top: 1em"></div>
    </div>`;

const handleMoveChanged = (result: CustomEvent<{ value: Array<[string, string]> }>) => {
    const target = document.querySelector("#action-button-message-pad");
    target!.innerHTML = "";

    target!.append(result.detail.value.map(([k, _]) => k).join(", "));
};

window.addEventListener("change", handleMoveChanged as unknown as EventListener);

type Story = StoryObj;

export const Default: Story = {
    render: () => container(html` <ak-sb-fruity .options=${goodForYou}></ak-sb-fruity>`),
};

declare global {
    interface HTMLElementTagNameMap {
        "ak-sb-fruity": AkSbFruity;
    }
}
