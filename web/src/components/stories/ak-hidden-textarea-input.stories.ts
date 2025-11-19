import "../ak-hidden-textarea-input.js";

import {
    type AkHiddenTextAreaInput,
    type AkHiddenTextAreaInputProps,
} from "../ak-hidden-textarea-input.js";

import { ifPresent } from "#elements/utils/attributes";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const metadata: Meta<AkHiddenTextAreaInputProps> = {
    title: "Components / <ak-hidden-textarea-input>",
    component: "ak-hidden-textarea-input",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Hidden Textarea Input Component

A textarea input field with a visibility control, so you can show/hide sensitive fields.
`,
            },
        },
        layout: "padded",
    },
    argTypes: {
        label: {
            control: "text",
            description: "Label text for the input field",
        },
        value: {
            control: "text",
            description: "Current value of the input",
        },
        revealed: {
            control: "boolean",
            description: "Whether the text is currently visible",
        },
        placeholder: {
            control: "text",
            description: "Placeholder text for the input",
        },
        required: {
            control: "boolean",
            description: "Whether the input is required",
        },
        inputHint: {
            control: "select",
            options: ["text", "code"],
            description: "Input type hint for styling and behavior",
        },
        showMessage: {
            control: "text",
            description: "Custom message for show action",
        },
        hideMessage: {
            control: "text",
            description: "Custom message for hide action",
        },
        rows: {
            control: { type: "number", min: 1, max: 50 },
            description: "Number of visible text lines",
        },
        cols: {
            control: { type: "number", min: 10, max: 200 },
            description: "Number of visible character width",
        },
        resize: {
            control: "select",
            options: ["none", "both", "horizontal", "vertical"],
            description: "How the textarea can be resized",
        },
        wrap: {
            control: "select",
            options: ["soft", "hard", "off"],
            description: "Text wrapping behavior",
        },
    },
};

export default metadata;

type Story = StoryObj<AkHiddenTextAreaInput>;

const Template: Story = {
    args: {
        label: "Hidden Textarea Input",
        value: "",
        revealed: false,
        rows: 4,
    },
    render: (args) => html`
        <ak-hidden-textarea-input
            label=${ifPresent(args.label)}
            value=${ifPresent(args.value)}
            ?revealed=${args.revealed}
            placeholder=${ifPresent(args.placeholder)}
            rows=${ifPresent(args.rows)}
            cols=${ifPresent(args.cols)}
            resize=${ifPresent(args.resize)}
            wrap=${ifPresent(args.wrap)}
            ?required=${args.required}
            input-hint=${ifPresent(args.inputHint)}
            show-message=${ifPresent(args.showMessage)}
            hide-message=${ifPresent(args.hideMessage)}
        ></ak-hidden-textarea-input>
    `,
};

export const SslCertificate: Story = {
    ...Template,
    args: {
        label: "SSL Certificate",
        value: `-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/heBjcOuMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTcwNTEwMTk0MDA2WhcNMTgwNTEwMTk0MDA2WjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMB4XDTE3MDUxMDE5NDAwNloXDTE4MDUxMDE5
NDAwNlowRTELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNV
BAoMGEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDCCASIwDQYJKoZIhvcNAQEBBQAD
ggEPADCCAQoCggEBALdUlNS31SzxwoFShahGfjHj6GgpcVbzL1Siq0Pqnf82T6M2
EDuneMLzAgMBAAECggEBAJkPFn6jeMHyiq0Pqnf82T6M2EDuneMLzAgMBAAECggE
BAJkPFn6jeMHyiq0Pqnf82T6M2EDuneMLzAgMBAAECggEBAJkPFn6jeMHyiq0Pqn
f82T6M2EDuneMLzAgMBAAECggEBAJkPFn6jeMHyiq0Pqnf82T6M2EDuneMLzAgM
BAAECggEBAJkPFn6jeMHyiq0Pqnf82T6M2EDuneMLzAgMBAAECggEBAJkPFn6jeM
Hyiq0Pqnf82T6M2EDuneMLzAgMBAAECggEBAJkPFn6jeMHyiq0Pqnf82T6M2EDu
neMLzAgMBAAECggEBAJkPFn6jeMHyiq0Pqnf82T6M2EDuneMLzAgMBAAECggEBAJ
kPFn6jeMHyiq0Pqnf82T6M2EDuneMLzAgMBAAE=
-----END CERTIFICATE-----`,
        inputHint: "code",
        rows: 15,
        resize: "vertical",
        showMessage: "Show certificate content",
        hideMessage: "Hide certificate content",
        autocomplete: "off",
    },
};
