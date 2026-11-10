import "./ak-icon.js";

import { IIcon } from "./ak-icon.js";

import { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

type IconFamily = "fa" | "fas" | "fab" | "pf";

const iconSizes = [
    "sm",
    "md",
    "lg",
    "xl",
    "1x",
    "2x",
    "3x",
    "4x",
    "5x",
    "6x",
    "7x",
    "8x",
    "9x",
    "10x",
] as const;

type IconSize = (typeof iconSizes)[number];

type IconVariant = "danger" | "warning" | "success" | "info" | "custom";
type IconEffect =
    | "beat"
    | "bounce"
    | "fade"
    | "beat-fade"
    | "flip"
    | "shake"
    | "spin"
    | "rotate-90"
    | "rotate-180"
    | "rotate-270"
    | "flip-horizontal"
    | "flip-vertical"
    | "flip-both"
    | "rotate-by";

type IconEffects = IconEffect | `${IconEffect} ${IconEffect}`;

type StoryProps = IIcon & {
    size?: IconSize;
    variant?: IconVariant;
    effect?: IconEffects;
};

const metadata: Meta<Partial<StoryProps>> = {
    title: "Elements/Icon",
    component: "ak-icon",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `
Displays icons from the Fontawesome and Patternfly font-based icon libraries.  Has an
aggressive alias system that prioritizes "fas" and "pf-icon" names where there were no
conflicts; for example, you can provide "birthday-cake" to the \`icon\` attribute and it
will find and display <ak-icon icon="birthday-cake"></ak-icon>`,
            },
        },
    },
    argTypes: {
        icon: {
            control: "text",
            description: "Icon name or alias (e.g., 'user', 'search', 'fa-home')",
            table: {
                type: { summary: "string" },
            },
        },
        family: {
            control: "select",
            description:
                "Icon family prefix - when provided with icon, creates explicit family/icon pair",
            options: ["", "fa", "fas", "fab", "pf"],
            table: {
                type: { summary: "IconFamily" },
            },
        },
        fallback: {
            control: "text",
            description: "Fallback icon class when resolution fails",
            table: {
                type: { summary: "string" },
                defaultValue: { summary: "fa fa-bug" },
            },
        },
        size: {
            control: "select",
            description: "Size variant affecting width, height, and font-size",
            options: ["", ...iconSizes],
            table: {
                type: { summary: "IconSize" },
            },
        },
        variant: {
            control: "select",
            description: "Semantic color variant",
            options: ["", "danger", "warning", "success", "info", "custom"],
            table: {
                type: { summary: "IconVariant" },
            },
        },
        effect: {
            control: "select",
            description: "Animation or transform effect (respects prefers-reduced-motion)",
            options: [
                "",
                "beat",
                "bounce",
                "fade",
                "beat-fade",
                "flip",
                "shake",
                "spin",
                "rotate-90",
                "rotate-180",
                "rotate-270",
                "flip-horizontal",
                "flip-vertical",
                "flip-both",
                "rotate-by",
            ],
            table: {
                type: { summary: "IconEffect" },
            },
        },
    },
    decorators: [
        (story) =>
            html`<div style="padding: 2rem; display: flex; align-items: center; gap: 1rem;">
                ${story()}
            </div>`,
    ],
};

export default metadata;

type Story = StoryObj<StoryProps>;

// Basic icon using alias system
export const Basic: Story = {
    args: {
        icon: "user",
    },
    render: (args: StoryProps) => html`
        <ak-icon
            icon=${ifDefined(args.icon)}
            family=${ifDefined(args.family)}
            fallback=${ifDefined(args.fallback)}
            size=${ifDefined(args.size)}
            variant=${ifDefined(args.variant)}
            effect=${ifDefined(args.effect)}
        ></ak-icon>
    `,
};

// Explicit family/icon usage
export const ExplicitFamilyIcon: Story = {
    args: {
        family: "fas",
        icon: "fa-home",
    },
    parameters: {
        docs: {
            description: {
                story: "Using explicit family and icon specification instead of alias resolution.",
            },
        },
    },
    render: (args: StoryProps) => html`
        <ak-icon family=${ifDefined(args.family)} icon=${ifDefined(args.icon)}></ak-icon>
    `,
};

// Size variants
export const SizeVariants: Story = {
    parameters: {
        docs: {
            description: {
                story: "Icon component with different size variants.",
            },
        },
    },
    render: () => html`
        <div style="display: block; clear: both">
            <h3 style="font-size: 1.25rem; font-weight: 900">Patternfly Icon Sizes</h3>
            <div style="display: flex; align-items: center; gap: 1rem; padding-bottom: 2rem;">
                <div
                    style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;"
                >
                    <ak-icon icon="user" size="sm"></ak-icon>
                    <span>Small</span>
                </div>
                <div
                    style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;"
                >
                    <ak-icon icon="user" size="md"></ak-icon>
                    <span>Medium</span>
                </div>
                <div
                    style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;"
                >
                    <ak-icon icon="user" size="lg"></ak-icon>
                    <span>Large</span>
                </div>
                <div
                    style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;"
                >
                    <ak-icon icon="user" size="xl"></ak-icon>
                    <span>Extra Large</span>
                </div>
            </div>
            <h3 style="font-size: 1.25rem; font-weight: 900">FontAwesome Icon Sizes</h3>
            <div style="display: flex; align-items: center; gap: 1rem;">
                ${iconSizes
                    .filter((sz) => /x$/.test(sz))
                    .map(
                        (sz) =>
                            html` <div
                                style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;"
                            >
                                <ak-icon icon="user" size="${sz}"></ak-icon>
                                <span>${sz.toUpperCase()}</span>
                            </div>`,
                    )}
            </div>
        </div>
    `,
};

// Semantic color variants
export const ColorVariants: Story = {
    parameters: {
        docs: {
            description: {
                story: "Icon component with semantic color variants.",
            },
        },
    },
    render: () => html`
        <div style="display: flex; align-items: center; gap: 2rem;">
            <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                <ak-icon icon="check-circle" variant="success" size="lg"></ak-icon>
                <span>Success</span>
            </div>
            <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                <ak-icon icon="exclamation-triangle" variant="warning" size="lg"></ak-icon>
                <span>Warning</span>
            </div>
            <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                <ak-icon icon="times-circle" variant="danger" size="lg"></ak-icon>
                <span>Danger</span>
            </div>
            <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                <ak-icon icon="info-circle" variant="info" size="lg"></ak-icon>
                <span>Info</span>
            </div>
            <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                <ak-icon icon="star" variant="custom" size="lg"></ak-icon>
                <span>Custom</span>
            </div>
        </div>
    `,
};

// Animation effects
export const AnimationEffects: Story = {
    parameters: {
        docs: {
            description: {
                story: "Icon component with various animation effects. Animations respect prefers-reduced-motion settings.",
            },
        },
    },
    render: () => html`
        <div
            style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem; text-align: center;"
        >
            <div>
                <ak-icon icon="fist-raised" effect="beat" size="lg" variant="danger"></ak-icon>
                <div>Beat</div>
            </div>
            <div>
                <ak-icon icon="tired" effect="bounce" size="lg"></ak-icon>
                <div>Bounce</div>
            </div>
            <div>
                <ak-icon icon="radiation-alt" effect="fade" size="lg"></ak-icon>
                <div>Fade</div>
            </div>
            <div>
                <ak-icon icon="heart" effect="beat-fade" size="lg" variant="danger"></ak-icon>
                <div>Beat Fade</div>
            </div>
            <div>
                <ak-icon icon="shield" effect="flip" size="lg"></ak-icon>
                <div>Flip</div>
            </div>
            <div>
                <ak-icon icon="bed" effect="shake" size="lg" variant="warning"></ak-icon>
                <div>Shake</div>
            </div>
            <div>
                <ak-icon icon="spinner" effect="spin" size="lg"></ak-icon>
                <div>Spin</div>
            </div>
            <div>
                <ak-icon icon="thumbs-down" effect="flip-down" size="lg"></ak-icon>
                <div>Flip Vertical</div>
            </div>
        </div>
    `,
};

// Transform effects
export const TransformEffects: Story = {
    parameters: {
        docs: {
            description: {
                story: "Icon component with transform effects (rotation and flipping).",
            },
        },
    },
    render: () => html`
        <div
            style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem; text-align: center;"
        >
            <div>
                <ak-icon icon="arrow-right" size="lg"></ak-icon>
                <div>Original</div>
            </div>
            <div>
                <ak-icon icon="arrow-right" effect="rotate-90" size="lg"></ak-icon>
                <div>Rotate 90°</div>
            </div>
            <div>
                <ak-icon icon="arrow-right" effect="rotate-180" size="lg"></ak-icon>
                <div>Rotate 180°</div>
            </div>
            <div>
                <ak-icon icon="arrow-right" effect="rotate-270" size="lg"></ak-icon>
                <div>Rotate 270°</div>
            </div>
            <div>
                <ak-icon icon="arrow-right" effect="flip-horizontal" size="lg"></ak-icon>
                <div>Flip Horizontal</div>
            </div>
            <div>
                <ak-icon icon="arrow-right" effect="flip-vertical" size="lg"></ak-icon>
                <div>Flip Vertical</div>
            </div>
            <div>
                <ak-icon icon="arrow-right" effect="flip-both" size="lg"></ak-icon>
                <div>Flip Both</div>
            </div>
            <div style="--fa-rotate-angle: 45deg;">
                <ak-icon icon="arrow-right" effect="rotate-by" size="lg"></ak-icon>
                <div>Custom Rotate (45°)</div>
            </div>
        </div>
    `,
};

// Transform effects
export const CombinedEffects: Story = {
    parameters: {
        docs: {
            description: {
                story: "Icon component with transform effects (rotation and flipping).",
            },
        },
    },
    render: () => html`
        <div
            style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem; text-align: center;"
        >
            <div>
                <ak-icon icon="bed" size="lg"></ak-icon>
                <div>No modifications</div>
            </div>
            <div>
                <ak-icon icon="bed" effect="flip-vertical shake" size="lg"></ak-icon>
                <div>Shake and Turn Upside Down</div>
            </div>
            <div>
                <ak-icon
                    icon="user-astronaut"
                    style="--fa-rotate-angle: 330deg"
                    effect="fade rotate-by"
                    size="lg"
                ></ak-icon>
                <div>Tilt (Custom Rotate) and Fade</div>
            </div>
        </div>
    `,
};

// Alias resolution examples
export const AliasExamples: Story = {
    parameters: {
        docs: {
            description: {
                story: "Examples of the extensive alias system supporting both FontAwesome and PatternFly icons.",
            },
        },
    },
    render: () => html`
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem;">
            <div style="text-align: center;">
                <h4>FontAwesome Aliases</h4>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon icon="user" size="lg"></ak-icon>
                        <code>icon="user"</code>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon icon="search" size="lg"></ak-icon>
                        <code>icon="search"</code>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon icon="home" size="lg"></ak-icon>
                        <code>icon="home"</code>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon icon="envelope" size="lg"></ak-icon>
                        <code>icon="envelope"</code>
                    </div>
                </div>
            </div>

            <div style="text-align: center;">
                <h4>PatternFly Aliases</h4>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon icon="cluster" size="lg"></ak-icon>
                        <code>icon="cluster"</code>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon icon="network" size="lg"></ak-icon>
                        <code>icon="network"</code>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon icon="monitoring" size="lg"></ak-icon>
                        <code>icon="monitoring"</code>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon icon="security" size="lg"></ak-icon>
                        <code>icon="security"</code>
                    </div>
                </div>
            </div>

            <div style="text-align: center;">
                <h4>Explicit Usage</h4>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon family="fas" icon="fa-cog" size="lg"></ak-icon>
                        <code>family="fas" icon="fa-cog"</code>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <ak-icon family="pf" icon="pf-icon-server" size="lg"></ak-icon>
                        <code>family="pf" icon="pf-icon-server"</code>
                    </div>
                </div>
            </div>
        </div>
    `,
};

// Fallback behavior
export const FallbackBehavior: Story = {
    args: {
        icon: "nonexistent-icon",
        fallback: "fa fa-question-circle",
    },
    parameters: {
        docs: {
            description: {
                story: "Demonstrates fallback behavior when icon resolution fails. Check browser console for warning message.",
            },
        },
    },
    render: (args: StoryProps) => html`
        <div style="display: flex; flex-direction: column; gap: 1rem; align-items: center;">
            <ak-icon
                icon=${ifDefined(args.icon)}
                fallback=${ifDefined(args.fallback)}
                size="lg"
            ></ak-icon>
            <div style="text-align: center;">
                <div>Requested: <code>icon="${args.icon}"</code></div>
                <div>Fallback: <code>fallback="${args.fallback}"</code></div>
                <div style="color: #666; font-size: 0.875rem;">
                    Check console for resolution warning
                </div>
            </div>
        </div>
    `,
};
