import { groupBy } from "@goauthentik/common/utils";
import { convertToSlug as slugify } from "@goauthentik/common/utils.js";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select";
import { SearchSelect } from "@goauthentik/elements/forms/SearchSelect/ak-search-select";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

type RawSample = [string, string[]];
type Sample = { name: string; pk: string; season: string[] };

// prettier-ignore
const groupedSamples: RawSample[] = [
    ["Spring", [
        "Apples", "Apricots", "Asparagus", "Avocados", "Bananas", "Broccoli",
        "Cabbage", "Carrots", "Celery", "Collard Greens", "Garlic", "Herbs", "Kale", "Kiwifruit", "Lemons",
        "Lettuce", "Limes", "Mushrooms", "Onions", "Peas", "Pineapples", "Radishes", "Rhubarb", "Spinach",
        "Strawberries", "Swiss Chard", "Turnips"]],
    ["Summer", [
        "Apples", "Apricots", "Avocados", "Bananas", "Beets", "Bell Peppers", "Blackberries", "Blueberries",
        "Cantaloupe", "Carrots", "Celery", "Cherries", "Corn", "Cucumbers", "Eggplant", "Garlic",
        "Green Beans", "Herbs", "Honeydew Melon", "Lemons", "Lima Beans", "Limes", "Mangos", "Okra", "Peaches",
        "Plums", "Raspberries", "Strawberries", "Summer Squash", "Tomatillos", "Tomatoes", "Watermelon",
        "Zucchini"]],
    ["Fall", [
        "Apples", "Bananas", "Beets", "Bell Peppers", "Broccoli", "Brussels Sprouts", "Cabbage", "Carrots",
        "Cauliflower", "Celery", "Collard Greens", "Cranberries", "Garlic", "Ginger", "Grapes", "Green Beans",
        "Herbs", "Kale", "Kiwifruit", "Lemons", "Lettuce", "Limes", "Mangos", "Mushrooms", "Onions",
        "Parsnips", "Pears", "Peas", "Pineapples", "Potatoes", "Pumpkin", "Radishes", "Raspberries",
        "Rutabagas", "Spinach", "Sweet Potatoes", "Swiss Chard", "Turnips", "Winter Squash"]],
    ["Winter", [
        "Apples", "Avocados", "Bananas", "Beets", "Brussels Sprouts", "Cabbage", "Carrots", "Celery",
        "Collard Greens", "Grapefruit", "Herbs", "Kale", "Kiwifruit", "Leeks", "Lemons", "Limes", "Onions",
        "Oranges", "Parsnips", "Pears", "Pineapples", "Potatoes", "Pumpkin", "Rutabagas",
        "Sweet Potatoes", "Swiss Chard", "Turnips", "Winter Squash"]]
];

// WAAAAY too many lines to turn the arrays above into a Sample of
// { name: "Apricots", pk: "apple", season: ["Spring", "Summer"] }
// but it does the job.

const samples = Array.from(
    groupedSamples
        .reduce((acc, sample) => {
            sample[1].forEach((item) => {
                const update = (thing: Sample) => ({
                    ...thing,
                    season: [...thing.season, sample[0]],
                });
                acc.set(
                    item,
                    update(acc.get(item) || { name: item, pk: slugify(item), season: [] }),
                );
                return acc;
            }, acc);
            return acc;
        }, new Map<string, Sample>())
        .values(),
);
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
