import "#elements/EmptyState";

import { DEFAULT_CONFIG } from "#common/api/config";
import { globalAK } from "#common/global";

import { WithBrandConfig } from "#elements/mixins/branding";
import { WithLicenseSummary } from "#elements/mixins/license";
import { AKModal } from "#elements/modals/ak-modal";
import { renderModal } from "#elements/modals/utils";
import { ThemedImage } from "#elements/utils/images";

import { AdminApi, CapabilitiesEnum, LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html, TemplateResult } from "lit";
import { styleMap } from "lit-html/directives/style-map.js";
import { customElement } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFAbout from "@patternfly/patternfly/components/AboutModalBox/about-modal-box.css";

const DEFAULT_BRAND_IMAGE = "/static/dist/assets/images/flow_background.jpg";

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
    } else if (version.buildHash) {
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
    static hostStyles = [
        css`
            :host {
                --ak-c-modal--BackgroundColor: var(--pf-global--palette--black-900);
            }
        `,
    ];

    static styles = [
        ...AKModal.styles,
        PFAbout,
        css`
            :host {
                height: 100%;
            }

            .pf-c-about-modal-box {
                --pf-c-about-modal-box--BackgroundColor: var(--ak-c-modal--BackgroundColor);
                width: unset;
                height: 100%;
                max-height: unset;
                max-width: unset;
                z-index: unset;
                position: unset;
                box-shadow: unset;
            }
        `,
    ];

    public static open = (event?: Event) => {
        const ownerDocument =
            event?.target instanceof HTMLElement ? event.target.ownerDocument : document;

        const tagName = window.customElements.getName(AboutModal);

        if (!tagName) {
            throw new TypeError("Custom element is not defined");
        }

        const modal = ownerDocument.createElement(tagName);

        return renderModal(modal, {
            ownerDocument,
        });
    };

    protected override renderCloseButton() {
        return null;
    }

    protected override render() {
        let product = this.brandingTitle;

        if (this.licenseSummary?.status !== LicenseSummaryStatusEnum.Unlicensed) {
            product += ` ${msg("Enterprise")}`;
        }

        return html`<div
            class="pf-c-about-modal-box"
            style=${styleMap({
                "--pf-c-about-modal-box__hero--sm--BackgroundImage": `url(${DEFAULT_BRAND_IMAGE})`,
            })}
            aria-labelledby="modal-title"
        >
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
            <div class="pf-c-about-modal-box__brand">
                ${ThemedImage({
                    src: this.brandingFavicon,
                    alt: msg("authentik Logo"),
                    className: "pf-c-about-modal-box__brand-image",
                    theme: this.activeTheme,
                    themedUrls: this.brandingFaviconThemedUrls,
                })}
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
