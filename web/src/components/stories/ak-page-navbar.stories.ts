import "#components/ak-page-navbar";

import { DefaultBrand } from "#common/ui/config";

import { AKPageNavbar } from "#components/ak-page-navbar";

import { CurrentBrand } from "@goauthentik/api";

import { Meta } from "@storybook/web-components";

import { html } from "lit";
import { customElement } from "lit/decorators.js";

const metadata: Meta<AKPageNavbar> = {
    title: "Components / Page Navbar",
    component: "ak-page-navbar",
    parameters: {
        docs: {
            description: {
                component: "A page navbar for the authentik web interface",
            },
        },
    },
};

export default metadata;

@customElement("story-ak-page-navbar")
class AKPageNavbarStory extends AKPageNavbar {
    brand: CurrentBrand = {
        ...DefaultBrand,
        brandingLogo: new URL(DefaultBrand.brandingLogo, "http://localhost:9000").toString(),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "story-ak-page-navbar": AKPageNavbarStory;
    }
}

export const SimplePageNavbar = () => {
    return html` <story-ak-page-navbar open @sidebar-toggle=${() => {}}> </story-ak-page-navbar> `;
};

export const PageNavbarWithIcon = () => {
    return html` <story-ak-page-navbar open @sidebar-toggle=${() => {}}> </story-ak-page-navbar> `;
};
