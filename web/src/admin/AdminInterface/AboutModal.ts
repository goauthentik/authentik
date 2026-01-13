import "#elements/EmptyState";

import { DEFAULT_CONFIG } from "#common/api/config";
import { globalAK } from "#common/global";

import { ModalButton } from "#elements/buttons/ModalButton";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithLicenseSummary } from "#elements/mixins/license";
import { ThemedImage } from "#elements/utils/images";

import { AdminApi, CapabilitiesEnum, LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";
import { until } from "lit/directives/until.js";

import PFAbout from "@patternfly/patternfly/components/AboutModalBox/about-modal-box.css";

@customElement("ak-about-modal")
export class AboutModal extends WithLicenseSummary(WithBrandConfig(ModalButton)) {
    static styles = [
        ...ModalButton.styles,
        PFAbout,
        css`
            .pf-c-about-modal-box {
                --pf-c-about-modal-box--BackgroundColor: var(--pf-global--palette--black-900);
            }

            .pf-c-about-modal-box__hero {
                background-image: url("/static/dist/assets/images/flow_background.jpg");
            }
            .pf-c-about-modal-box__brand {
                --pf-c-about-modal-box__brand-image--Height: 6.25rem;
            }
            .pf-c-about-modal-box__brand i {
                font-size: var(--pf-c-about-modal-box__brand-image--Height);
            }
        `,
    ];

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
            [msg("UI Version"), import.meta.env.AK_VERSION],
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

    #contentRef = createRef<HTMLDivElement>();

    #backdropListener = (event: PointerEvent) => {
        // We only want to close the modal when the backdrop is clicked, not when it's children are clicked.

        if (this.#contentRef.value?.contains(event.target as Node)) {
            return;
        }
        this.close();
    };

    protected override renderModal() {
        let product = this.brandingTitle;

        if (this.licenseSummary?.status !== LicenseSummaryStatusEnum.Unlicensed) {
            product += ` ${msg("Enterprise")}`;
        }
        return html`<div class="pf-c-backdrop" @click=${this.#backdropListener}>
            <div class="pf-l-bullseye">
                <div
                    ${ref(this.#contentRef)}
                    class="pf-c-about-modal-box"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="modal-title"
                >
                    <div class="pf-c-about-modal-box__brand">
                        ${ThemedImage({
                            src: this.brandingFavicon,
                            alt: msg("authentik Logo"),
                            className: "pf-c-about-modal-box__brand-image",
                            theme: this.activeTheme,
                        })}
                    </div>
                    <div class="pf-c-about-modal-box__close">
                        <button class="pf-c-button pf-m-plain" type="button" @click=${this.close}>
                            <i class="fas fa-times" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="pf-c-about-modal-box__header">
                        <h1 class="pf-c-title pf-m-4xl" id="modal-title">${product}</h1>
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
