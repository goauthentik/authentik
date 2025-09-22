import { AkControlElement } from "#elements/AkControlElement";
import { type Spread } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { FooterLink } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, queryAll } from "lit/decorators.js";

import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface IFooterLinkInput {
    footerLink: FooterLink;
}

const LEGAL_SCHEMES = ["http://", "https://", "mailto:"];
const hasLegalScheme = (url: string) =>
    LEGAL_SCHEMES.some((scheme) => url.substr(0, scheme.length).toLowerCase() === scheme);

@customElement("ak-admin-settings-footer-link")
export class FooterLinkInput extends AkControlElement<FooterLink> {
    static styles = [
        PFBase,
        PFInputGroup,
        PFFormControl,
        css`
            .pf-c-input-group input#linkname {
                flex-grow: 1;
                width: 8rem;
            }
        `,
    ];

    @property({ type: Object, attribute: false })
    footerLink: FooterLink = {
        name: "",
        href: "",
    };

    @queryAll(".ak-form-control")
    controls?: HTMLInputElement[];

    json() {
        return Object.fromEntries(
            Array.from(this.controls ?? []).map((control) => [control.name, control.value]),
        ) as unknown as FooterLink;
    }

    get isValid() {
        const href = this.json()?.href ?? "";
        return hasLegalScheme(href) && URL.canParse(href);
    }

    render() {
        const onChange = () => {
            this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
        };

        return html` <div class="pf-c-input-group">
            <input
                type="text"
                @change=${onChange}
                value=${this.footerLink.name}
                id="linkname"
                class="pf-c-form-control ak-form-control"
                name="name"
                placeholder=${msg("Link Title")}
                tabindex="1"
            />
            <input
                type="url"
                @change=${onChange}
                value="${ifPresent(this.footerLink.href)}"
                class="pf-c-form-control ak-form-control pf-m-monospace"
                autocomplete="off"
                required
                placeholder=${msg("URL")}
                name="href"
                tabindex="1"
            />
        </div>`;
    }
}

export function akFooterLinkInput(properties: IFooterLinkInput) {
    return html`<ak-admin-settings-footer-link
        ${spread(properties as unknown as Spread)}
    ></ak-admin-settings-footer-link>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-settings-footer-link": FooterLinkInput;
    }
}
