import { Meta } from "@storybook/web-components";

import { html } from "lit";

import "./ak-spinner-button";
import AKSpinnerButton from "./ak-spinner-button";

const metadata: Meta<AKSpinnerButton> = {
    title: "Elements / Spinner Button",
    component: "ak-spinner-button",
    parameters: {
        docs: {
            description: {
                component: "A four-state button for asynchronous operations",
            },
        },
    },
    argTypes: {
        callAction: {
            type: "function",
            description:
                "Asynchronous function that takes no arguments and returns a promise.  The contents of the completed Promise will be sent with the ak-button-success event.",
        },
    },
};

export default metadata;

export const ButtonWithSuccess = () => {
    const run = () =>
        new Promise<void>(function (resolve) {
            setTimeout(function () {
                resolve();
            }, 3000);
        });

    return html`<div style="background: #fff; padding: 4em">
        <ak-spinner-button class="pf-m-primary" .callAction=${run}>3 Seconds</ak-spinner-button>
    </div>`;
};

export const ButtonWithReject = () => {
    const run = () =>
        new Promise((resolve, reject) => {
            setTimeout(() => {
                reject("Rejected!");
            }, 3000);
        });

    return html`<div style="background: #fff; padding: 4em">
        <ak-spinner-button class="pf-m-secondary" .callAction=${run}>3 Seconds</ak-spinner-button>
    </div>`;
};
