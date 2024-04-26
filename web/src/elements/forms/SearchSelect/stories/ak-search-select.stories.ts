import { groupBy } from "@goauthentik/common/utils";
import { convertToSlug as slugify } from "@goauthentik/common/utils.js";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select";
import { SearchSelect } from "@goauthentik/elements/forms/SearchSelect/ak-search-select";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import { sampleData } from "./sampleData.js";

type RawSample = [string, string[]];

type Sample = { name: string; pk: string; season: string[] };

const samples = sampleData.map(({ produce, seasons, desc }) => ({
    name: produce,
    pk: produce.replace(/\s+/, "").toLowerCase(),
    season: seasons,
}));
samples.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));

// All we need is a promise to return our dataset. It doesn't have to be a class-based method a'la
// the authentik API.

const getSamples = (query = "") =>
    Promise.resolve(
        samples.filter((s) =>
            query !== "" ? s.name.toLowerCase().includes(query.toLowerCase()) : true,
        ),
    );

const metadata: Meta<SearchSelect<Sample>> = {
    title: "Elements / Search Select ",
    component: "ak-search-select",
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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const displayChange = (ev: any) => {
    document.getElementById("message-pad")!.innerText = `Value selected: ${JSON.stringify(
        ev.detail.value,
        null,
        2,
    )}`;
};

export const Default = () => {
    return container(
        html`<ak-search-select
            .fetchObjects=${getSamples}
            .renderElement=${(sample: Sample) => sample.name}
            .value=${(sample: Sample) => sample.pk}
            @ak-change=${displayChange}
        ></ak-search-select>`,
    );
};

export const Grouped = () => {
    return container(
        html`<ak-search-select
            .fetchObjects=${getSamples}
            .renderElement=${(sample: Sample) => sample.name}
            .value=${(sample: Sample) => sample.pk}
            .groupBy=${(samples: Sample[]) =>
                groupBy(samples, (sample: Sample) => sample.season[0] ?? "")}
            @ak-change=${displayChange}
        ></ak-search-select>`,
    );
};

export const Selected = () => {
    return container(
        html`<ak-search-select
            .fetchObjects=${getSamples}
            .renderElement=${(sample: Sample) => sample.name}
            .value=${(sample: Sample) => sample.pk}
            .selected=${(sample: Sample) => sample.pk === "herbs"}
            @ak-change=${displayChange}
        ></ak-search-select>`,
    );
};
