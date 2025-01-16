import "@goauthentik/elements/messages/MessageContainer";
import { Meta, StoryObj } from "@storybook/web-components";
import { slug } from "github-slugger";

import { LitElement, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { Pagination } from "@goauthentik/api";

import "../ak-dual-select";
import { AkDualSelect } from "../ak-dual-select";
import { DualSelectPaginatorNavEvent } from "../events";
import type { DualSelectPair } from "../types";

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
        pages: {
            type: "string",
            description: "An authentik pagination object.",
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

    @state()
    page: Pagination;

    constructor() {
        super();
        this.page = {
            count: this.options.length,
            current: 1,
            startIndex: 1,
            endIndex: this.options.length > this.pageLength ? this.pageLength : this.options.length,
            next: this.options.length > this.pageLength ? 2 : 0,
            previous: 0,
            totalPages: Math.ceil(this.options.length / this.pageLength),
        };
        this.onNavigation = this.onNavigation.bind(this);
        this.addEventListener(DualSelectPaginatorNavEvent.eventName, this.onNavigation);
    }

    onNavigation(evt: DualSelectPaginatorNavEvent) {
        const current = evt.page;
        const index = current - 1;
        if (index * this.pageLength > this.options.length) {
            console.warn(
                `Attempted to index from ${index} for options length ${this.options.length}`,
            );
            return;
        }
        const endCount = this.pageLength * (index + 1);
        const endIndex = Math.min(endCount, this.options.length);

        this.page = {
            ...this.page,
            current,
            startIndex: this.pageLength * index + 1,
            endIndex,
            next: (index + 1) * this.pageLength > this.options.length ? 0 : current + 1,
            previous: index,
        };
    }

    get pageoptions() {
        return this.options.slice(
            this.pageLength * (this.page.current - 1),
            this.pageLength * this.page.current,
        );
    }

    render() {
        return html`<ak-dual-select
            .options=${this.pageoptions}
            .pages=${this.page}
        ></ak-dual-select>`;
    }
}

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
        <ak-message-container></ak-message-container>
        ${testItem}
        <p>Messages received from the button:</p>
        <div id="action-button-message-pad" style="margin-top: 1em"></div>
    </div>`;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleMoveChanged = (result: any) => {
    const target = document.querySelector("#action-button-message-pad");
    target!.innerHTML = "";
    // @ts-ignore
    target!.append(result.detail.value.map(([k, _]) => k).join(", "));
};

window.addEventListener("change", handleMoveChanged);

type Story = StoryObj;

export const Default: Story = {
    render: () => container(html` <ak-sb-fruity .options=${goodForYou}></ak-sb-fruity>`),
};

declare global {
    interface HTMLElementTagNameMap {
        "ak-sb-fruity": AkSbFruity;
    }
}
