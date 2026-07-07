import "@goauthentik/truncator/lit";

import type { AKTruncate } from "@goauthentik/truncator/lit";
import { Truncate, TruncateIPAddress, TruncateURL } from "@goauthentik/truncator/lit";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html, type TemplateResult } from "lit";

const metadata: Meta<AKTruncate> = {
    title: "Elements / Truncate",
    component: "ak-truncate",
    parameters: {
        docs: {
            description: {
                component:
                    "Pixel-aware, structure-aware text truncation. Each value type has a dedicated element (`ak-truncate-url`, `ak-truncate-ip-address`, …) over a shared base. The source is the `value` property or slotted text. Drag the right edge of a container to watch it re-truncate live.",
            },
        },
    },
};

export default metadata;

const SAMPLES = {
    "url": "https://sub.example.com/app/dashboard?session=8f3b1c9d2e4a5f6b&ref=nav",
    "hash": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "mac-address": "00:1a:2b:3c:4d:5e",
    "ip-address": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
    "email": "firstname.lastname@averylongcompany.example.com",
    "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "string": "The quick brown fox jumps over the lazy dog",
} as const;

const resizable = (contents: TemplateResult) => html`
    <div
        style="width: 320px; resize: horizontal; overflow: auto; border: 1px solid var(--pf-global--BorderColor--100, #888); padding: 0.75em; font-family: var(--pf-global--FontFamily--monospace, monospace);"
    >
        ${contents}
    </div>
`;

interface PlaygroundArgs {
    value: string;
    ellipsis: string;
    width: number;
}

export const Playground: StoryObj<PlaygroundArgs> = {
    args: {
        value: SAMPLES.url,
        ellipsis: "…",
        width: 260,
    },
    argTypes: {
        value: { control: "text" },
        ellipsis: { control: "text" },
        width: { control: { type: "range", min: 48, max: 640, step: 8 } },
    },
    render: ({ value, ellipsis, width }) => html`
        <div
            style="width: ${width}px; resize: horizontal; overflow: auto; border: 1px solid var(--pf-global--BorderColor--100, #888); padding: 0.75em; font-family: var(--pf-global--FontFamily--monospace, monospace);"
        >
            <ak-truncate-url .value=${value} .ellipsis=${ellipsis}></ak-truncate-url>
        </div>
    `,
};

export const AllKinds: StoryObj = {
    render: () =>
        resizable(html`
            <div
                style="display: grid; grid-template-columns: auto 1fr; gap: 0.5em 1em; align-items: center;"
            >
                <span>url</span>
                <ak-truncate-url value=${SAMPLES.url}></ak-truncate-url>
                <span>hash</span>
                <ak-truncate-hash value=${SAMPLES.hash}></ak-truncate-hash>
                <span>uuid</span>
                <ak-truncate-uuid value=${SAMPLES.uuid}></ak-truncate-uuid>
                <span>mac</span>
                <ak-truncate-mac-address value=${SAMPLES["mac-address"]}></ak-truncate-mac-address>
                <span>ip</span>
                <ak-truncate-ip-address value=${SAMPLES["ip-address"]}></ak-truncate-ip-address>
                <span>email</span>
                <ak-truncate-email value=${SAMPLES.email}></ak-truncate-email>
                <span>ua</span>
                <ak-truncate-user-agent value=${SAMPLES["user-agent"]}></ak-truncate-user-agent>
                <span>string</span>
                <ak-truncate value=${SAMPLES.string}></ak-truncate>
            </div>
        `),
};

export const SlottedContent: StoryObj = {
    render: () =>
        resizable(html`
            <ak-truncate-ip-address>${SAMPLES["ip-address"]}</ak-truncate-ip-address>
        `),
};

/**
 * The `createTruncatorFC` helpers render the matching element from a plain
 * call, and fall back to a "-" for empty input.
 */
export const FunctionForm: StoryObj = {
    render: () =>
        resizable(html`
            <div style="display: grid; gap: 0.5em;">
                ${TruncateURL(SAMPLES.url)} ${TruncateIPAddress(SAMPLES["ip-address"])}
                ${Truncate("")}
            </div>
        `),
};
