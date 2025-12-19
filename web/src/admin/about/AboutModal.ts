import "#elements/EmptyState";

import { DEFAULT_CONFIG } from "#common/api/config";
import { globalAK } from "#common/global";

import { ModalButton } from "#elements/buttons/ModalButton";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithLicenseSummary } from "#elements/mixins/license";
import { AKModal } from "#elements/modals/ak-modal";

import { AdminApi, CapabilitiesEnum, LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";
import { until } from "lit/directives/until.js";

import PFAbout from "@patternfly/patternfly/components/AboutModalBox/about-modal-box.css";

type AboutEntry = [label: string, content: string | TemplateResult];

async function fetchAboutDetails(): Promise<AboutEntry[]> {
    const api = new AdminApi(DEFAULT_CONFIG);
    const [status, version] = await Promise.all([
        api.adminSystemRetrieve(),
        api.adminVersionRetrieve(),
    ]);

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

@customElement("ak-about-modal")
export class AboutModal extends WithLicenseSummary(WithBrandConfig(AKModal)) {
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
        `,
    ];

    #contentRef = createRef<HTMLDivElement>();

    protected override render() {
        let product = this.brandingTitle;

        if (this.licenseSummary?.status !== LicenseSummaryStatusEnum.Unlicensed) {
            product += ` ${msg("Enterprise")}`;
        }
        return html` <div ${ref(this.#contentRef)} class="pf-c-about-modal-box">
            <div class="pf-c-about-modal-box__brand">
                <img
                    class="pf-c-about-modal-box__brand-image"
                    src=${this.brandingFavicon}
                    alt="${msg("authentik Logo")}"
                />
            </div>
            <div class="pf-c-about-modal-box__close">
                <button
                    class="pf-c-button pf-m-plain"
                    type="button"
                    @click=${this.closeListener}
                    aria-label=${msg("Close dialog")}
                >
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
                            fetchAboutDetails().then((entries) => {
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
        </div>`;
    }
}
