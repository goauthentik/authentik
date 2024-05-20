import "@goauthentik/elements/messages/MessageContainer";
import { Meta } from "@storybook/web-components";

import { TemplateResult, html } from "lit";

import "../ak-slug-input";
import AkSlugInput from "../ak-slug-input";
import "../ak-text-input";

const metadata: Meta<AkSlugInput> = {
    title: "Components / Slug Input",
    component: "ak-slug-input",
    parameters: {
        docs: {
            description: {
                component: "A stylized value control for slug input",
            },
        },
    },
};

export default metadata;

const container = (testItem: TemplateResult) =>
    html` <div style="background: #000; padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>

        ${testItem}

        <ul id="text-message-pad" style="color: #fff; margin-top: 1em"></ul>
    </div>`;

export const SlugInput = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const displayChange = (ev: any) => {
        document.getElementById("text-message-pad")!.innerText = `Value selected: ${JSON.stringify(
            ev.target.value,
            null,
            2,
        )}`;
    };

    return container(
        html`<ak-text-input
                label="Test Text Input"
                name="ak-test-text-input"
                help="Type your input here"
            ></ak-text-input>
            <ak-slug-input
                @input=${displayChange}
                source="ak-text-input[name=ak-test-text-input]"
                label="Test Text Input"
                name="ak-test-text-input"
                help="Here should be the slugified version"
            ></ak-slug-input> `,
    );
};
