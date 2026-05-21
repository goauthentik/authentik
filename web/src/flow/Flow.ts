import "#elements/LoadingOverlay";
import "#elements/locale/ak-locale-select";
import "#flow/inspector/FlowInspectorButton";
import "#flow/FlowExecutor";
import "#flow/tabs/broadcast";

import { FlowWebsocketClientController } from "./controllers/FlowWebsocketClientController";
import Styles from "./FlowExecutor.css" with { type: "bundled-text" };

import { globalAK } from "#common/global";
import { applyBackgroundImageProperty } from "#common/theme";
import { AKSessionAuthenticatedEvent } from "#common/ws/events";

import { listen } from "#elements/decorators/listen";
import { light } from "#elements/directives/light";
import { Interface } from "#elements/Interface";
import { WithBrandConfig } from "#elements/mixins/branding";
import { SlottedTemplateResult } from "#elements/types";
import { ThemedImage } from "#elements/utils/images";

import { AKFlowInfoUpdateEvent, AKFlowLoadingEvent } from "#flow/events";

import { ConsoleLogger } from "#logger/browser";

import { ContextualFlowInfo, FlowLayoutEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

import PFBackgroundImage from "@patternfly/patternfly/components/BackgroundImage/background-image.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

/// <reference types="../../types/lit.d.ts" />

// We only need this to re-assure the type checker that we've received an object
// from the messaging class. ContextualFlowInfo is almost entirely optional
// fields, and we destructure it while ignoring any unexpected fields.

const isContextualFlowInfo = (v: unknown): v is ContextualFlowInfo =>
    typeof v === "object" && v !== null;

/**
 * The application shell for authentik flows and the Flow Executor.
 *
 * @remarks
 *
 * - Provides the Brand context
 * - Provides the Flow Websocket Controller for messages and notifications
 * - Provides the Theme controller
 * - Houses the Flow Inspector controls
 * - Houses the Locale controls
 * - Sets document title for tabs and windows
 * - Sets the layout according to the global settings
 * - Initializes the FlowExecutor and places it in the lightDOM
 *
 * @attr {string} slug - The slug of the flow to execute. Prop-drilled to the executor.
 *
 * @attr {FlowLayoutEnum} data-layout - Page layout variant. Defaults to
 * `globalAK().flow.layout` or just `stacked`
 *
 * @slot footer - The page-level footer content.  Currently filled by `ak-brand-links`.
 *
 * @part main - The main container for the flow content.
 *
 * @part flow-executor - Wrapper around ak-flow-executor
 *
 * @part content - The container for the stage content.
 *
 * @part content-iframe - The iframe element when using a frame background layout.
 *
 * @part footer - The footer container.
 *
 * @part locale-select - The locale select component.
 *
 * @part branding - The branding element, used for the background image in some layouts.
 *
 * @part loading-overlay - The loading overlay element.
 *
 * @part locale-select-label - The label of the locale select component.
 *
 * @part locale-select-select - The select element of the locale select component.
 *
 * NOTE: This is the application shell, the top-level component. From here, we
 * invoke the flow-executor in-line in the template rendered, but use the
 * `light()` directive to inject it into the Flow element's lightDOM, and a slot
 * is emplaced where the flow-executor's part of the template would go. This
 * enables password managers to traverse down into the flow and its stages
 * without having to cross or know about shadowDOM boundaries.
 *
 */
@customElement("ak-flow")
export class Flow extends WithBrandConfig(Interface) {
    //#region Static

    public static readonly DefaultLayout: FlowLayoutEnum =
        globalAK()?.flow?.layout || FlowLayoutEnum.Stacked;

    public static styles: CSSResult[] = [
        PFLogin,
        PFDrawer,
        PFButton,
        PFTitle,
        PFList,
        PFBackgroundImage,
        Styles,
    ];

    //#endregion

    //#region Properties

    @property({ type: String })
    public slug: string = window.location.pathname.split("/")[3];

    // Reflection is required to trigger the correct behavior with CSS;
    @property({ attribute: "data-layout", reflect: true })
    public layout: FlowLayoutEnum = Flow.DefaultLayout;

    @state()
    protected loading = true;

    @state()
    public title: string = "";

    @state()
    public background: ContextualFlowInfo["background"];

    @state()
    protected backgroundThemedUrls?: ContextualFlowInfo["backgroundThemedUrls"];

    #abortController: AbortController | null = null;

    readonly #wsController = new FlowWebsocketClientController(this);

    protected readonly logger = ConsoleLogger.prefix("flow");

    //#endregion

    //#region Render

    constructor() {
        super();
        this.addController(this.#wsController);
    }

    #handleFlowUpdate = (event: AKFlowInfoUpdateEvent) => {
        const { flowInfo } = event;
        if (!isContextualFlowInfo(flowInfo)) {
            return;
        }

        // The `!== undefined` is deliberate; if a flow update has no change to
        // any of these, they should inherit the previous stage's decorative
        // state.

        if ("title" in flowInfo && flowInfo.title !== undefined) {
            this.title = flowInfo.title;
        }

        if ("background" in flowInfo && flowInfo.background !== undefined) {
            this.background = flowInfo.background;
        }

        if ("backgroundThemedUrls" in flowInfo && flowInfo.backgroundThemedUrls !== undefined) {
            this.backgroundThemedUrls = flowInfo.backgroundThemedUrls;
        }

        if ("layout" in flowInfo && flowInfo.layout !== undefined) {
            this.layout = flowInfo.layout;
        }
    };

    #handleLoading = (event: AKFlowLoadingEvent) => {
        this.loading = true;

        // The event comes with a payload: a protected boolean promise that
        // reflects the pending state of whatever triggered the "loading" state
        // deep down. Neat trick here: we simply await on it and, when it's
        // done, we trigger a state change. No other system needs to track
        // "loading" states at all.

        event.awaiter.finally(() => {
            this.loading = false;
        });
    };

    public override connectedCallback(): void {
        super.connectedCallback();

        // Do not remove. This can happen if Flow is reparented as the result of
        // a higher-level component slot change. While there's no current design
        // that would make that happen, it's not worth removing this code to
        // take that risk.
        if (this.#abortController) {
            this.#abortController.abort();
        }

        this.#abortController = new AbortController();
        const { signal } = this.#abortController;
        this.addEventListener(AKFlowInfoUpdateEvent.eventName, this.#handleFlowUpdate, { signal });
        this.addEventListener(AKFlowLoadingEvent.eventName, this.#handleLoading, { signal });
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#abortController?.abort();
        this.#abortController = null;
    }

    @listen(AKSessionAuthenticatedEvent)
    protected onSessionAuthenticated = () => {
        if (document.hidden) {
            this.logger.debug("Reloading after session authenticated in background tab");
            window.location.reload();
        }
    };

    private get layoutUsesSidebarFrames(): boolean {
        return (
            this.layout === FlowLayoutEnum.SidebarLeftFrameBackground ||
            this.layout === FlowLayoutEnum.SidebarRightFrameBackground
        );
    }

    #synchronizeBackground() {
        if (!(this.background || this.backgroundThemedUrls) || this.layoutUsesSidebarFrames) return;

        const background = this.backgroundThemedUrls?.[this.activeTheme] || this.background;

        // Storybook has a different document structure.
        const target =
            import.meta.env.AK_BUNDLER === "storybook"
                ? this.closest<HTMLDivElement>(".docs-story")
                : this.ownerDocument.body;

        applyBackgroundImageProperty(background, { target });
    }

    protected renderHeader() {
        return ThemedImage({
            src: this.brandingLogo,
            alt: msg("authentik Logo"),
            className: "branding-logo",
            theme: this.activeTheme,
            themedUrls: this.brandingLogoThemedUrls,
        });
    }

    // Only used by the `sidebar_*_frame_backgrounds` to give customers a place to put their
    // branding visuals, if they like.
    //
    protected renderFrameBackground() {
        const { layout, background, layoutUsesSidebarFrames } = this;

        return guard([layout, background], () => {
            if (!(layoutUsesSidebarFrames && background)) return nothing;

            return html`
                <div class="ak-c-login__content" part="content">
                    <iframe
                        class="ak-c-login__content-iframe"
                        part="content-iframe"
                        name="flow-content-frame"
                        src=${background}
                    ></iframe>
                </div>
            `;
        });
    }

    protected renderFooter() {
        return guard([this.layout], () => {
            return html`<footer
                aria-label=${msg("Site footer")}
                name="site-footer"
                part="footer"
                class="pf-c-login__footer ${this.layout === FlowLayoutEnum.Stacked
                    ? "pf-m-dark"
                    : ""}"
            >
                <slot name="footer"></slot>
            </footer>`;
        });
    }

    protected override render(): SlottedTemplateResult {
        const { loading } = this;

        return html`<ak-locale-select
                part="locale-select"
                exportparts="label:locale-select-label,select:locale-select-select"
                class="pf-m-dark"
            ></ak-locale-select>
            <ak-flow-inspector-button></ak-flow-inspector-button>
            ${this.renderFrameBackground()}
            <header class="pf-c-login__header"></header>
            <main
                data-layout=${this.layout}
                class="pf-c-login__main"
                aria-label=${msg("Authentication form")}
                part="main"
            >
                <div class="pf-c-login__main-header pf-c-brand" part="branding">
                    ${this.renderHeader()}
                </div>
                ${loading
                    ? html`<ak-loading-overlay part="loading-overlay"></ak-loading-overlay>`
                    : nothing}
                <div part="flow-executor">
                    ${light(html`<ak-flow-executor slug=${this.slug}></ak-flow-executor>`)}
                </div>
            </main>
            ${this.renderFooter()}`;
    }

    //#endregion

    public override updated(changed: PropertyValues<this>) {
        super.updated(changed);
        if (changed.has("title")) {
            const brand = this.brandingTitle;
            document.title = this.title ? `${this.title} - ${brand}` : brand;
        }

        if (changed.has("activeTheme") || changed.has("background" satisfies keyof Flow)) {
            this.#synchronizeBackground();
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow": Flow;
    }
}
