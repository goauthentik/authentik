import "./ak-drawer";

import { DrawerExpandRequest } from "./ak-drawer.component";

import type { Meta, StoryObj } from "@storybook/web-components-vite";

import { html, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const toggle = (e: Event) => {
    const button = e.target as HTMLButtonElement;
    button.dispatchEvent(new DrawerExpandRequest());
};

const contentBlock = html`
    <div style="padding: 1rem;">
        <h2>Main Content</h2>
        <p><button @click=${toggle}>Toggle Drawer</button></p>
        <p>
            This is the drawer's main: fill it by inserting slotted content without a slot name.
            This is the part that stays visible most of the time.
        </p>
        <p>
            Macaroon lollipop croissant sweet biscuit croissant chocolate cake. Cake cake pastry
            soufflé pudding. Tiramisu lollipop chocolate cake toffee oat cake muffin topping tootsie
            roll. Carrot cake bonbon chupa chups sugar plum fruitcake. Brownie sweet halvah oat cake
            cheesecake topping chocolate. Wafer macaroon topping lollipop powder cupcake sugar plum
            donut. Muffin wafer icing danish jelly-o bonbon. Powder shortbread brownie caramels
            tootsie roll dragée liquorice. Cake lemon drops powder danish toffee.
        </p>
    </div>
`;

const panelBlock = html`
    <style>
        [slot="panel"] {
            padding: 1rem;
            background-color: var(--pf-v5-global--BackgroundColor--200, #f0f0f0);
        }
    </style>
    <div slot="panel">
        <h3>Panel Content</h3>
        <p>This is the side panel. This is where you put the secondary information.</p>
        <ul>
            <li>
                Seasonal, steamed, con panna and rich ut aged cup decaffeinated single origin con
                panna bar
            </li>
            <li>Skinny mazagran whipped, black iced beans carajillo eu cream</li>
            <li>Americano pumpkin spice milk ristretto caffeine single shot</li>
        </ul>
        <p><button @click=${toggle}>Toggle Drawer</button></p>
    </div>
`;

interface DrawerProps {
    expanded?: boolean;
    inline?: boolean;
    static?: boolean;
    resizable?: boolean;
    width?: string;
    position?: string;
    content?: TemplateResult;
    panel?: TemplateResult;
}

const meta = {
    title: "Components/Drawer",
    component: "ak-drawer",
    tags: ["autodocs"],
    decorators: [
        (story) =>
            html`<div style="min-height: 400px; border: 1px solid #d2d2d2; overflow: hidden;">
                ${story()}
            </div>`,
    ],
    argTypes: {
        expanded: { control: "boolean" },
        position: {
            control: { type: "select" },
            options: ["right", "left", "bottom"],
        },
        inline: { control: "boolean" },
        static: { control: "boolean" },
        resizable: { control: "boolean" },
        width: {
            control: { type: "select" },
            options: ["25", "33", "50", "66", "75", "100"],
        },
    },
} satisfies Meta;

export default meta;
type Story = StoryObj;

const Template: Story = {
    args: {
        expanded: false,
        inline: false,
        static: false,
        resizable: false,
        width: undefined,
        position: undefined,
        content: contentBlock,
        panel: panelBlock,
    },
    render: (args) => {
        return html` <ak-drawer
            ?expanded=${args.expanded}
            ?inline=${args.inline}
            ?resizable=${args.resizable}
            position=${ifDefined(args.position)}
            width=${ifDefined(args.width)}
        >
            ${args.content} ${args.panel}
        </ak-drawer>`;
    },
};

export const Default: Story = {
    render: () => html` <ak-drawer> ${contentBlock} ${panelBlock} </ak-drawer> `,
};

export const story = (args: DrawerProps = {}, name?: string): Story => ({
    ...Template,
    ...(name ? { name } : {}),
    args: {
        ...Template.args,
        ...args,
    },
});

export const Expanded: Story = story({ expanded: true });

export const PanelLeft: Story = story({ expanded: true, position: "left" });

export const PanelBottom = story({ expanded: true, position: "bottom" });

export const Inline = story({ expanded: true, inline: true });

export const Static = story({ expanded: true, static: true });

export const Resizable = story({ expanded: true, resizable: true });

export const ResizableLeft = story({ expanded: true, resizable: true, position: "left" });

export const ResizableBottom = story({ expanded: true, resizable: true, position: "bottom" });

export const CustomWidth = story({ expanded: true, width: "33" });

export const ResponsiveWidth = story({ expanded: true, width: "75-on-xl" });
