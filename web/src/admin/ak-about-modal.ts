import "#elements/ak-progress-bar";

import { DEFAULT_CONFIG } from "#common/api/config";
import { globalAK } from "#common/global";

import { asInvoker } from "#elements/dialogs";
import { AKModal } from "#elements/dialogs/ak-modal";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithLicenseSummary } from "#elements/mixins/license";
import { SlottedTemplateResult } from "#elements/types";
import { DefaultFlowBackground, ThemedImage } from "#elements/utils/images";

import {
    AdminApi,
    CapabilitiesEnum,
    LicenseSummaryStatusEnum,
    SystemInfo,
    Version,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { ref } from "lit-html/directives/ref.js";
import { styleMap } from "lit-html/directives/style-map.js";
import { until } from "lit-html/directives/until.js";
import { customElement, state } from "lit/decorators.js";

import PFAbout from "@patternfly/patternfly/components/AboutModalBox/about-modal-box.css";

type AboutEntry = [label: string, content?: SlottedTemplateResult];

function renderEntry([label, content = null]: AboutEntry): SlottedTemplateResult {
    return html`<dt>${label}</dt>
        <dd>${content === null ? msg("Loading...") : content}</dd>`;
}

@customElement("ak-about-modal")
export class AboutModal extends WithLicenseSummary(WithBrandConfig(AKModal)) {
    public override formatARIALabel = () => msg("About authentik");

    public static hostStyles = [
        ...AKModal.hostStyles,
        css`
            .ak-c-dialog:has(ak-about-modal) {
                --ak-c-dialog--BackgroundColor: var(--pf-global--palette--black-900);
                --ak-c-dialog--BorderColor: var(--pf-global--palette--black-600);
            }
        `,
    ];

    public static styles = [
        ...AKModal.styles,
        PFAbout,
        css`
            :host {
                height: 100%;
            }

            .pf-c-about-modal-box {
                --pf-c-about-modal-box--BackgroundColor: var(--ak-c-dialog--BackgroundColor);
                width: unset;
                height: 100%;
                max-height: unset;
                max-width: unset;
                z-index: unset;
                position: unset;
                box-shadow: unset;
            }

            [part="brand"] {
                position: relative;
            }

            [part="loading-bar"] {
                position: absolute;
                z-index: 1;
                inset-block-start: 0;
                inset-inline: 0;
            }
        `,
    ];

    public static ariaLabel = msg("About authentik");

    public static open = asInvoker(AboutModal);

    #api = new AdminApi(DEFAULT_CONFIG);

    protected canDebug = globalAK().config.capabilities.includes(CapabilitiesEnum.CanDebug);

    @state()
    protected version: Version | null = null;

    @state()
    protected systemInfo: SystemInfo | null = null;

    @state()
    protected refreshPromise: Promise<[Version, SystemInfo]> | null = null;

    public refresh = (): void => {
        const versionPromise = this.#api.adminVersionRetrieve();
        const systemInfoPromise = this.#api.adminSystemRetrieve();

        this.refreshPromise = Promise.all([versionPromise, systemInfoPromise]).then((result) => {
            this.version = result[0];
            this.systemInfo = result[1];

            return result;
        });
    };

    public connectedCallback(): void {
        super.connectedCallback();
        this.refresh();
    }

    protected renderVersionInfo = () => {
        const { version } = this;

        let build: SlottedTemplateResult = null;

        if (this.canDebug) {
            build = msg("Development");
        } else if (version?.buildHash) {
            build = html`<a
                rel="noopener noreferrer"
                href="https://github.com/goauthentik/authentik/commit/${version.buildHash}"
                target="_blank"
                >${version.buildHash}</a
            >`;
        } else if (version) {
            build = msg("Release");
        }

        const entries: AboutEntry[] = [
            [msg("Server Version"), version?.versionCurrent],
            [msg("Build"), build],
        ];

        return entries.map(renderEntry);
    };

    protected renderSystemInfo = () => {
        const { runtime } = this.systemInfo || {};

        const sslLabel = runtime
            ? `${runtime.opensslVersion} ${runtime.opensslFipsEnabled ? "FIPS" : ""}`
            : null;

        const entries: AboutEntry[] = [
            [msg("Python version"), runtime?.pythonVersion],
            [msg("Platform"), runtime?.platform],
            [msg("OpenSSL"), sslLabel],
            [
                msg("Kernel"),
                runtime?.uname ?? html`<div style="min-height: 3em;">${msg("Loading...")}</div>`,
            ],
        ];

        return entries.map(renderEntry);
    };

    //#region Renderers

    protected override renderCloseButton() {
        return null;
    }

    protected renderLoadingBar(): SlottedTemplateResult {
        return until(
            this.refreshPromise?.then(() => null),
            html`<ak-progress-bar
                part="loading-bar"
                indeterminate
                ?inert=${!!this.systemInfo && !!this.version}
                label=${msg("Loading")}
            ></ak-progress-bar>`,
        );
    }

    protected override render() {
        let product = this.brandingTitle;

        if (this.licenseSummary?.status !== LicenseSummaryStatusEnum.Unlicensed) {
            product += ` ${msg("Enterprise")}`;
        }

        return html`<div
            ${ref(this.scrollContainerRef)}
            class="pf-c-about-modal-box"
            style=${styleMap({
                "--pf-c-about-modal-box__hero--sm--BackgroundImage": `url(${DefaultFlowBackground})`,
            })}
            part="box"
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
            <div class="pf-c-about-modal-box__brand" part="brand">
                ${this.renderLoadingBar()}
                ${ThemedImage({
                    src: this.brandingFavicon,
                    alt: msg("authentik Logo"),
                    className: "pf-c-about-modal-box__brand-image",
                    theme: this.activeTheme,
                    themedUrls: this.brandingFaviconThemedUrls,
                })}
            </div>
            <div class="pf-c-about-modal-box__header" part="header">
                <h1 class="pf-c-title pf-m-4xl" id="modal-title" part="title">${product}</h1>
            </div>
            <div class="pf-c-about-modal-box__hero"></div>
            <div class="pf-c-about-modal-box__content">
                <div class="pf-c-about-modal-box__body">
                    <div class="pf-c-content">
                        <dl>
                            <dt>${msg("UI Version")}</dt>
                            <dd>${import.meta.env.AK_VERSION}</dd>
                            ${until(
                                this.refreshPromise?.then(this.renderVersionInfo),
                                this.renderVersionInfo(),
                            )}
                            ${until(
                                this.refreshPromise?.then(this.renderSystemInfo),
                                this.renderSystemInfo(),
                            )}
                        </dl>
                    </div>
                </div>
                <p class="pf-c-about-modal-box__strapline"></p>
            </div>
        </div>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-about-modal": AboutModal;
    }
}
