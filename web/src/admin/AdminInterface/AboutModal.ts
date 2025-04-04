import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { VERSION } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import "@goauthentik/elements/EmptyState";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";
import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";
import { DefaultBrand } from "@goauthentik/elements/sidebar/SidebarBrand";

import { msg } from "@lit/localize";
import { TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFAbout from "@patternfly/patternfly/components/AboutModalBox/about-modal-box.css";

import { AdminApi, CapabilitiesEnum, LicenseSummaryStatusEnum } from "@goauthentik/api";

@customElement("ak-about-modal")
export class AboutModal extends WithLicenseSummary(WithBrandConfig(ModalButton)) {
    static get styles() {
        return ModalButton.styles.concat(
            PFAbout,
            css`
                .pf-c-about-modal-box__hero {
                    background-image: url("/static/dist/assets/images/flow_background.jpg");
                }
            `,
        );
    }

    async getAboutEntries(): Promise<[string, string | TemplateResult][]> {
        const status = await new AdminApi(DEFAULT_CONFIG).adminSystemRetrieve();
        const version = await new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve();
        let build: string | TemplateResult = msg("Release");
        if (globalAK().config.capabilities.includes(CapabilitiesEnum.CanDebug)) {
            build = msg("Development");
        } else if (version.buildHash !== "") {
            build = html`<a
                rel="noopener noreferrer"
                href="https://github.com/goauthentik/authentik/commit/${version.buildHash}"
                target="_blank"
                >${version.buildHash}</a
            >`;
        }
        return [
            [msg("Version"), version.versionCurrent],
            [msg("UI Version"), VERSION],
            [msg("Build"), build],
            [msg("Python version"), status.runtime.pythonVersion],
            [msg("Platform"), status.runtime.platform],
            [msg("Kernel"), status.runtime.uname],
            [
                msg("OpenSSL"),
                `${status.runtime.opensslVersion} ${status.runtime.opensslFipsEnabled ? "FIPS" : ""}`,
            ],
        ];
    }

    renderModal() {
        let product = globalAK().brand.brandingTitle || DefaultBrand.brandingTitle;
        if (this.licenseSummary.status != LicenseSummaryStatusEnum.Unlicensed) {
            product += ` ${msg("Enterprise")}`;
        }
        return html`<div
            class="pf-c-backdrop"
            @click=${(e: PointerEvent) => {
                e.stopPropagation();
                this.closeModal();
            }}
        >
            <div class="pf-l-bullseye">
                <div class="pf-c-about-modal-box" role="dialog" aria-modal="true">
                    <div class="pf-c-about-modal-box__brand">
                        <img
                            class="pf-c-about-modal-box__brand-image"
                            src=${this.brand?.brandingFavicon ?? DefaultBrand.brandingFavicon}
                            alt="${msg("authentik Logo")}"
                        />
                    </div>
                    <div class="pf-c-about-modal-box__close">
                        <button
                            class="pf-c-button pf-m-plain"
                            type="button"
                            @click=${() => {
                                this.open = false;
                            }}
                        >
                            <i class="fas fa-times" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="pf-c-about-modal-box__header">
                        <h1 class="pf-c-title pf-m-4xl">${product}</h1>
                    </div>
                    <div class="pf-c-about-modal-box__hero"></div>
                    <div class="pf-c-about-modal-box__content">
                        <div class="pf-c-about-modal-box__body">
                            <div class="pf-c-content">
                                ${until(
                                    this.getAboutEntries().then((entries) => {
                                        return html`<dl>
                                            ${entries.map(([label, value]) => {
                                                return html`<dt>${label}</dt>
                                                    <dd>${value}</dd>`;
                                            })}
                                        </dl>`;
                                    }),
                                    html`<ak-empty-state loading></ak-empty-state>`,
                                )}
                            </div>
                        </div>
                        <p class="pf-c-about-modal-box__strapline"></p>
                    </div>
                </div>
            </div>
        </div>`;
    }
}
