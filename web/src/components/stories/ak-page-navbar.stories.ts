import { DefaultBrand } from "#common/ui/config";
import "#components/ak-page-header";
import { AKPageNavbar } from "#components/ak-page-navbar";
import { Meta } from "@storybook/web-components";

import { html } from "lit";
import { customElement } from "lit/decorators.js";

import { CurrentBrand } from "@goauthentik/api";

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
    return html`
        <story-ak-page-navbar open @sidebar-toggle=${() => {}}>
            <ak-page-header header="Page Title" description="Page Description"> </ak-page-header>
        </story-ak-page-navbar>
    `;
};

export const PageNavbarWithIcon = () => {
    return html`
        <story-ak-page-navbar open @sidebar-toggle=${() => {}}>
            <ak-page-header
                header="Page Title"
                description="Page Description"
                icon="pf-icon pf-icon-user"
            >
            </ak-page-header>
        </story-ak-page-navbar>
    `;
};
