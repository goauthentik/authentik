import "#elements/forms/SearchSelect/ak-search-select-view";

import { groupedSampleData, sampleData } from "./sampleData.js";

import { SearchSelectView } from "#elements/forms/SearchSelect/ak-search-select-view";

import { Meta } from "@storybook/web-components";
import { slug } from "github-slugger";

import { html, TemplateResult } from "lit";

const metadata: Meta<SearchSelectView> = {
    title: "Elements / Search Select / View Handler ",
    component: "ak-search-select-view",
    parameters: {
        docs: {
            description: {
                component: "An implementation of the Patternfly search select pattern",
            },
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

        <ul id="message-pad" style="margin-top: 1em"></ul>
    </div>`;

const longGoodForYouPairs = {
    grouped: false,
    options: sampleData.map(({ produce }) => [slug(produce), produce]),
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const displayChange = (ev: any) => {
    document.getElementById("message-pad")!.innerText = `Value selected: ${JSON.stringify(
        ev.value,
        null,
        2,
    )}`;
};

export const Default = () => {
    return container(
        html`<ak-search-select-view
            .options=${longGoodForYouPairs}
            blankable
            @ak-search-select-select=${displayChange}
        ></ak-search-select-view>`,
    );
};

export const DescribedGroups = () => {
    return container(
        html`<ak-search-select-view
            .options=${groupedSampleData}
            blankable
            @ak-search-select-select=${displayChange}
        ></ak-search-select-view>`,
    );
};
