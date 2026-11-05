/**
 * @file Storybook stories and documentation for Tooltip components.
 */

import "../ak-tooltip";
import type { Tooltip } from "../ak-tooltip";
import { akTooltip } from "../ak-tooltip";

import { type Placement, placements } from "@floating-ui/utils";
import { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

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
            description:
                "Delay in ms before showing tooltip (prevents spamming the viewer) (--ak-c-tooltip--ShowDelay)",
        },
        hideDelay: {
            control: "number",
            description: "Delay in ms before hiding tooltip (--ak-c-tooltip--HideDelay)",
        },
        hideArrow: {
            control: "boolean",
            description: "Hide the arrow pointing to the anchor",
        },
    },
};

export default metadata;

type Story = StoryObj<Tooltip>;

const button = (label: string) =>
    html`<button style="padding: 0.5rem 1rem; font-size: 1rem; cursor: pointer;">${label}</button>`;

export const Default: Story = {
    tags: ["!autodocs"],
    args: {
        content: "Behold! A button!",
        placement: "top",
        trigger: "hover",
        showDelay: 500,
        hideDelay: 100,
        hideArrow: false,
    },
    render: (args) =>
        html`<div style="padding: 6rem; display: flex; justify-content: center;">
            <ak-tooltip
                placement=${ifDefined(args.placement)}
                trigger=${ifDefined(args.trigger)}
                style="--ak-c-tooltip--ShowDelay: ${args.showDelay}ms; --ak-c-tooltip--HideDelay: ${args.hideDelay}ms;"
                ?hide-arrow=${!!args.hideArrow}
            >
                ${button("Reveal!")}
                <span slot="tooltip">${args.content}</span>
            </ak-tooltip>
        </div>`,
};

export const WithSlottedContent: Story = {
    args: {
        placement: "bottom",
    },
    render: (args) =>
        html`<div style="padding: 6rem; display: flex; justify-content: center;">
            <ak-tooltip placement=${ifDefined(args.placement)}>
                ${button("Hover for rich content")}
                <div slot="tooltip">
                    <strong>Rich Tooltip Content</strong>
                    <p style="margin: 4px 0 0 0; font-size: 12px;">
                        This <em>color</em> is <span style="color: lightsalmon">fishy</span>.
                    </p>
                </div>
            </ak-tooltip>
        </div>`,
};

export const FocusTrigger: Story = {
    args: {
        placement: "right",
        trigger: "focus",
    },
    render: (args) =>
        html`<style>
                .pulse {
                    display: inline-block;
                    font-size: 2rem;
                    animation: pulse-animation 1s infinite;
                }

                @media (prefers-reduced-motion) {
                    .pulse {
                        animation: none;
                    }
                }

                @keyframes pulse-animation {
                    50% {
                        transform: scale(1.3);
                    }
                }
            </style>
            <div style="padding: 6rem; display: flex; justify-content: center;">
                <ak-tooltip
                    placement=${ifDefined(args.placement)}
                    trigger=${ifDefined(args.trigger)}
                >
                    ${button("Tab to me")}
                    <span slot="tooltip" class="pulse">❤️</span>
                </ak-tooltip>
            </div>`,
};

const placementCell = (placement: Placement) =>
    html`<ak-tooltip placement=${placement}>
        ${button(placement)}
        <span slot="tooltip">Placement: ${placement}</span>
    </ak-tooltip>`;

export const AllPlacements: Story = {
    render: () =>
        html`<div
            style="padding: 6rem; display: grid; grid-template-columns: repeat(3, auto); gap: 4rem 6rem; justify-content: center; align-items: center; justify-items: center;"
        >
            ${placementCell("top-start")} ${placementCell("top")} ${placementCell("top-end")}
            ${placementCell("left-start")}
            <div></div>
            ${placementCell("right-start")} ${placementCell("left")}
            <div style="padding: 1rem; border: 2px dashed #ccc;">The Middle!</div>
            ${placementCell("right")} ${placementCell("left-end")}
            <div></div>
            ${placementCell("right-end")} ${placementCell("bottom-start")}
            ${placementCell("bottom")} ${placementCell("bottom-end")}
        </div>`,
};

export const OverflowContainer: Story = {
    render: () =>
        html`<div style="padding: 6rem;">
            <p style="margin-bottom: 20px;">
                <strong>Overflow test:</strong> The tooltip escapes the overflow:hidden container
                but only when the Popover API is supported. This also demonstrates how to override
                the tooltip's styling with a <code>style</code> attribute on the component.
            </p>

            <div style="overflow: hidden; border: 2px solid #ddd; padding: 20px; max-width: 300px;">
                <p>This container has <code>overflow: hidden</code></p>

                <ak-tooltip
                    style="--ak-c-tooltip__content--BackgroundColor: repeating-linear-gradient(45deg, hsl(43, 74%, 42%), hsl(43, 74%, 42%) 0.5rem, hsl(201, 12%, 40%) 0.5rem, hsl(201, 12%, 40%) 1rem);"
                    placement="right"
                >
                    ${button("Hover me")}
                    <div slot="tooltip" style="white-space: nowrap; font-weight: bold;">
                        Warning! The creature has escaped containment.<br />The creature has escaped
                        containment!
                    </div>
                </ak-tooltip>
            </div>
        </div>`,
};

export const OverflowContainerViaBuilder: Story = {
    render: () =>
        html`<div style="padding: 6rem;">
            <p style="margin-bottom: 20px;">
                <strong>Builder:</strong> The same overflow test, built with
                <code>akTooltip()</code> and styled through a <code>class</code> on the component.
            </p>
            <style>
                .creature {
                    --ak-c-tooltip__content--BackgroundColor: linear-gradient(
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
            <div style="overflow: hidden; border: 2px solid #ddd; padding: 20px; max-width: 300px;">
                <p>This container has <code>overflow: hidden</code></p>
                ${akTooltip({
                    anchor: button("Hover me"),
                    content: html`<span style="font-weight: bold;"
                        >[Keanu Reeves voice] "Whoa."</span
                    >`,
                    placement: "top",
                    class: "creature",
                })}
            </div>
        </div>`,
};
