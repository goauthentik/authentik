import { groupBy } from "@goauthentik/common/utils.js";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select";
import { SearchSelect } from "@goauthentik/elements/forms/SearchSelect/ak-search-select";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select-ez";
import { type ISearchSelectApi } from "@goauthentik/elements/forms/SearchSelect/ak-search-select-ez";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import { sampleData } from "./sampleData.js";

type Sample = { name: string; pk: string; season: string[] };

const samples = sampleData.map(({ produce, seasons }) => ({
    name: produce,
    pk: produce.replace(/\s+/, "").toLowerCase(),
    season: seasons,
}));
samples.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));

// All we need is a promise to return our dataset. It doesn't have to be a class-based method a'la
// the authentik API.

const getSamples = (query = "") => {
    if (query === "") {
        return Promise.resolve(samples);
    }
    const check = new RegExp(query);
    return Promise.resolve(samples.filter((s) => check.test(s.name)));
};

const metadata: Meta<SearchSelect<Sample>> = {
    title: "Elements / Search Select / API Interface",
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
    document.getElementById("message-pad")!.innerText =
        `Value selected: ${JSON.stringify(ev.detail.value, null, 2)}`;
};

export const Default = () =>
    container(
        html`<ak-search-select
            .fetchObjects=${getSamples}
            .renderElement=${(sample: Sample) => sample.name}
            .value=${(sample: Sample) => sample.pk}
            @ak-change=${displayChange}
        ></ak-search-select>`,
    );

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

export const GroupedAndEz = () => {
    const config: ISearchSelectApi<Sample> = {
        fetchObjects: getSamples,
        renderElement: (sample: Sample) => sample.name,
        value: (sample: Sample | undefined) => sample?.pk ?? "",
        groupBy: (samples: Sample[]) =>
            groupBy(samples, (sample: Sample) => sample.season[0] ?? ""),
    };

    return container(
        html`<ak-search-select-ez
            .config=${config}
            @ak-change=${displayChange}
        ></ak-search-select-ez>`,
    );
};

export const SelectedAndBlankable = () => {
    return container(
        html`<ak-search-select
            blankable
            .fetchObjects=${getSamples}
            .renderElement=${(sample: Sample) => sample.name}
            .value=${(sample: Sample) => sample.pk}
            .selected=${(sample: Sample) => sample.pk === "herbs"}
            @ak-change=${displayChange}
        ></ak-search-select>`,
    );
};
