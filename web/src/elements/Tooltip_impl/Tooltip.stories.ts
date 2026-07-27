/**
 * @file Storybook stories and documentation for Tooltip components.
 */

import "../Tooltip";

import type { Tooltip } from "../Tooltip";
import { akTooltip } from "../Tooltip";

import { placements } from "@floating-ui/utils";
import { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const describe = (story: string, tag = "story") => ({
    parameters: { docs: { description: { [tag]: story } } },
});

const DESCRIPTION =
    "A tooltip component that uses the HTML dialog element for positioning and the top layer. Tooltips can be triggered by hover or focus events.";

const metadata: Meta<Tooltip> = {
    title: "Elements / Tooltip",
    component: "ak-tooltip",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: DESCRIPTION,
            },
        },
    },
    argTypes: {
        content: {
            control: "text",
            description: "Text content of the tooltip (deprecated - prefer slots)",
        },
        htmlFor: {
            control: "text",
            description: "ID or selector of the anchor element",
        },
        placement: {
            control: "select",
            options: placements,
            description: "Where to position the tooltip relative to the anchor",
        },
        trigger: {
            control: "select",
            options: ["hover", "focus"],
            description: "What event triggers the tooltip",
        },
        showDelay: {
            control: "number",
            description: "Delay in ms before showing tooltip (prevents spam)",
        },
        hideDelay: {
            control: "number",
            description: "Delay in ms before hiding tooltip",
        },
        hideArrow: {
            control: "boolean",
            description: "Hide the arrow pointing to the anchor",
        },
    },
};

export default metadata;

type Story = StoryObj<Tooltip>;

const Template: Story = {
    render: (args) => html`
        <div style="padding: 6rem; display: flex; flex-direction: column; justify-content: center;">
            <button
                id=${ifDefined(args.htmlFor)}
                style="padding: 0.5rem 1rem; font-size: 1rem; cursor: pointer; width: fit-content;"
            >
                Reveal!
            </button>
            <ak-tooltip
                for=${ifDefined(args.htmlFor)}
                placement=${ifDefined(args.placement)}
                trigger=${ifDefined(args.trigger)}
                show-delay=${ifDefined(args.showDelay)}
                hide-delay=${ifDefined(args.hideDelay)}
                ?hide-arrow=${!!args.hideArrow}
                >${args.content}
            </ak-tooltip>
        </div>
    `,
};

export const Default: Story = {
    ...Template,
    tags: ["!autodocs"],
    args: {
        content: "Behold! A button!",
        htmlFor: "demo-button",
        placement: "top",
        trigger: "hover",
        showDelay: 500,
        hideDelay: 100,
        hideArrow: false,
    },
};

export const WithSlottedContent: Story = {
    args: {
        htmlFor: "slotted-button",
        placement: "bottom",
    },
    render: (args) => html`
        <div style="padding: 100px; display: flex; justify-content: center;">
            <button
                id="slotted-button"
                style="padding: 10px 20px; font-size: 16px; cursor: pointer;"
            >
                Hover for rich content
            </button>
            <ak-tooltip for=${args.htmlFor} placement=${args.placement}>
                <strong>Rich Tooltip Content</strong>
                <p style="margin: 4px 0 0 0; font-size: 12px;">
                    This <em>color</em> is <span style="color: lightsalmon">fishy</span>.
                </p>
            </ak-tooltip>
        </div>
    `,
};

export const AllPlacements: Story = {
    render: () => html`
        <div
            style="padding: 150px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; justify-items: center; align-items: center;"
        >
            <button id="top-left-btn" style="padding: 8px 16px;">Top Left</button>
            <button id="top-btn" style="padding: 8px 16px;">Top</button>
            <button id="top-right-btn" style="padding: 8px 16px;">Top Right</button>

            <button id="left-btn" style="padding: 8px 16px;">Left</button>
            <div style="padding: 20px; border: 2px dashed #ccc;">The Middle!</div>
            <button id="right-btn" style="padding: 8px 16px;">Right</button>

            <button id="bottom-left-btn" style="padding: 8px 16px;">Bottom Left</button>
            <button id="bottom-btn" style="padding: 8px 16px;">Bottom</button>
            <button id="bottom-right-btn" style="padding: 8px 16px;">Bottom Right</button>

            <ak-tooltip
                for="top-left-btn"
                content="Top left placement"
                tabindex="0"
                placement="top-start"
            ></ak-tooltip>
            <ak-tooltip
                for="top-btn"
                content="Top placement"
                tabindex="0"
                placement="top"
            ></ak-tooltip>
            <ak-tooltip
                for="top-right-btn"
                content="Top right placement"
                tabindex="0"
                placement="top-end"
            ></ak-tooltip>

            <ak-tooltip
                for="left-btn"
                content="Left placement"
                tabindex="0"
                placement="left"
            ></ak-tooltip>
            <ak-tooltip
                for="right-btn"
                content="Right placement"
                tabindex="0"
                placement="right"
            ></ak-tooltip>

            <ak-tooltip
                for="bottom-left-btn"
                content="Bottom left placement"
                tabindex="0"
                placement="bottom-start"
            ></ak-tooltip>
            <ak-tooltip
                for="bottom-btn"
                content="Bottom placement"
                tabindex="0"
                placement="bottom"
            ></ak-tooltip>
            <ak-tooltip
                for="bottom-right-btn"
                content="Bottom right placement"
                tabindex="0"
                placement="bottom-end"
            ></ak-tooltip>
        </div>
    `,
};

export const OverflowContainer: Story = {
    render: () => html`
        <div style="padding: 100px;">
            <p style="margin-bottom: 20px;">
                <strong>Overflow test:</strong> The tooltip escapes the overflow:hidden container
                thanks to the dialog element's top layer. This also demonstrates how to override the
                tooltip's styling with a <code>style</code> attribute on the component.
            </p>
            <div style="overflow: hidden; border: 2px solid #ddd; padding: 20px; max-width: 300px;">
                <p>This container has <code>overflow: hidden</code></p>
                <button id="overflow-btn" style="padding: 10px 20px; margin-top: 10px;">
                    Hover me
                </button>
            </div>

            <ak-tooltip
                style="--pf-v5-c-tooltip__content--BackgroundColor: repeating-linear-gradient(45deg, hsl(43, 74%, 42%), hsl(43, 74%, 42%) 0.5rem, hsl(201, 12%, 40%) 0.5rem, hsl(201, 12%, 40%) 1rem);"
                for="overflow-btn"
                placement="right"
                ><div style="white-space: nowrap; font-weight: bold;">
                    Warning! The creature has escaped containment.<br />The creature has escaped
                    containment!
                </div></ak-tooltip
            >
        </div>
    `,
};

export const OverflowContainerViaBuilder: Story = {
    render: () => {
        const tooltipContent = {
            content: html`<div style="white-space: nowrap; font-weight: bold; color: black;">
                [Keanu Reeves voice] "Whoa."
            </div>`,
            htmlFor: "overflow-button-2",
            placement: "top",
            class: "creature",
        };

        return html`
            <div style="padding: 100px;">
                <p style="margin-bottom: 20px;">
                    <strong>Overflow test:</strong> The tooltip escapes the overflow:hidden
                    container thanks to the dialog element's top layer. This also demonstrates how
                    to override the tooltip's styling with a <code>class</code> attribute on the
                    component.
                </p>
                <div
                    style="overflow: hidden; border: 2px solid #ddd; padding: 20px; max-width: 300px;"
                >
                    <p>This container has <code>overflow: hidden</code></p>
                    <button id="overflow-button-2" style="padding: 10px 20px; margin-top: 10px;">
                        Hover me
                    </button>
                </div>

                <style>
                    .creature {
                        --pf-v5-c-tooltip__content--BackgroundColor: linear-gradient(
                            132deg,
                            #000000,
                            #00ff00,
                            #0000ff,
                            #e60073,
                            #ff0000,
                            #ffffff
                        );
                    }
                </style>
                ${akTooltip(tooltipContent)}
            </div>
        `;
    },
};
