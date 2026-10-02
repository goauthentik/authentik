import "#flow/FormStatic";
import "#flow/components/ak-flow-card";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

import { pluckErrorDetail } from "#common/errors/network";

import { akEmptyState } from "#elements/EmptyState";
import { ListenerController } from "#elements/utils/listenerController";

import { AKFormErrors, ErrorProp } from "#components/ak-field-errors";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";
import Styles from "#flow/stages/captcha/CaptchaStage.css";
import { CapController } from "#flow/stages/captcha/controllers/cap";
import {
    CaptchaController,
    CaptchaControllerConstructor,
    CaptchaHandlerHost,
} from "#flow/stages/captcha/controllers/CaptchaController";
import { GReCaptchaController } from "#flow/stages/captcha/controllers/grecaptcha";
import { HCaptchaController } from "#flow/stages/captcha/controllers/hcaptcha";
import { TurnstileController } from "#flow/stages/captcha/controllers/turnstile";
import { loadCaptchaScript } from "#flow/stages/captcha/script-loader";
import { CAPTCHA_SLOT } from "#flow/stages/captcha/shared";

import { ConsoleLogger } from "#logger/browser";

import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";

import { LOCALE_STATUS_EVENT, LocaleStatusEventDetail, msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

export type TokenListener = (token: string) => void;

/**
 * The nearest ancestor that sits in the document tree rather than in a shadow root.
 *
 * Returns `null` while the node is detached, when there is no document-tree host to speak
 * of yet.
 */
function documentTreeHost(node: Node): Element | null {
    let current: Node = node;

    for (;;) {
        const root = current.getRootNode();

        if (!(root instanceof ShadowRoot)) {
            return current.isConnected && current instanceof Element ? current : null;
        }

        current = root.host;
    }
}

/**
 * Pin a vendor frame to the size it declared.
 *
 * reCAPTCHA and hCaptcha set anchor frame size through `width`/`height` attributes.
 * Those are only hints, so author CSS can override them.
 *
 * PatternFly's reset applies `max-width: 100%` and `height: auto` to iframes.
 * For iframes, `height: auto` falls back to the 150px default, which can leave a blank
 * area below the widget.
 *
 * We only pin frames that declare a size and do not already set one inline.
 * Turnstile already sets inline size.
 */
function pinFrameSize(node: Node): void {
    if (!(node instanceof HTMLIFrameElement)) return;

    for (const dimension of ["width", "height"] as const) {
        const declared = node.getAttribute(dimension);

        if (!declared || node.style[dimension]) continue;

        node.style[dimension] = `${declared}px`;
    }
}

/**
 * Watch a container for vendor iframes as they are added.
 *
 * Each iframe is pinned to its declared size, then passed to the controller for
 * vendor-specific adjustments.
 *
 * We observe instead of doing a one-time scan after `mount()` because frame creation
 * timing differs by vendor, and `reset()` may recreate frames later.
 */
function observeFrames(
    container: HTMLElement,
    decorate: (frame: HTMLIFrameElement) => void,
): MutationObserver {
    const visit = (node: Node) => {
        if (!(node instanceof HTMLIFrameElement)) return;

        pinFrameSize(node);
        decorate(node);
    };

    const observer = new MutationObserver((mutations) => {
        for (const { addedNodes } of mutations) {
            for (const node of addedNodes) {
                visit(node);

                if (node instanceof Element) {
                    node.querySelectorAll("iframe").forEach(visit);
                }
            }
        }
    });

    observer.observe(container, { childList: true, subtree: true });

    return observer;
}

@customElement("ak-stage-captcha")
export class CaptchaStage
    extends BaseStage<CaptchaChallenge, CaptchaChallengeResponseRequest>
    implements CaptchaHandlerHost
{
    public static readonly styles: CSSResult[] = [
        // ---
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        Styles,
    ];

    /**
     * Set of Captcha provider controllers.
     *
     * Order is a tie-breaker for the global-matching fallback in
     * {@linkcode CaptchaController.resolve}; challenges whose script URL is recognized are
     * matched exactly regardless of position.
     */
    public static readonly controllers = new Set<CaptchaControllerConstructor>([
        // ---
        HCaptchaController,
        GReCaptchaController,
        TurnstileController,
        CapController,
    ]);

    #logger = ConsoleLogger.prefix("flow:captcha");

    //#region Properties

    @property({ type: Boolean })
    public embedded = false;

    #tokenListener: TokenListener = (token: string) => {
        this.host.submit({ component: "ak-stage-captcha", token });
    };

    /**
     * Called when the provider challenge is solved.
     *
     * Returns the current token listener instead of a listener captured at mount time.
     */
    public get onTokenChange(): TokenListener {
        return this.#reportToken;
    }

    public set onTokenChange(listener: TokenListener) {
        this.#tokenListener = listener;
    }

    #reportToken = (token: string): void => {
        this.#solved = true;
        this.#tokenListener(token);
    };

    @property()
    public onLoad?: () => void;

    @property({ attribute: false })
    public refreshedAt = new Date();

    //#endregion

    //#region State

    @property({ attribute: false })
    public error: ErrorProp | null = null;

    /**
     * Whether the provider has reported its widget as rendered.
     */
    @state()
    protected widgetLoaded = false;

    /**
     * The currently active Captcha controller, if any.
     */
    @state()
    protected activeController: CaptchaController | null = null;

    #container?: HTMLDivElement;
    #frameObserver?: MutationObserver;
    #listenController = new ListenerController();

    /**
     * Guards against a slow script load resolving after the challenge has moved on.
     */
    #loadGeneration = 0;

    /**
     * The challenge the active controller was built for.
     */
    #loadedChallenge: CaptchaChallenge | null = null;

    /**
     * Whether the provider has issued a token for the current widget.
     */
    #solved = false;

    //#endregion

    //#region Container

    /**
     * The element a provider renders its widget into.
     *
     * This container is attached to the flow executor (in the document tree), then shown
     * inside the card through {@linkcode CAPTCHA_SLOT}. reCAPTCHA and hCaptcha look up
     * elements through `document`; if the container lives inside a `ShadowRoot`, the
     * widget may render but never complete verification. Slotting keeps the container in
     * the document tree while displaying it in the card.
     */
    protected get container(): HTMLDivElement {
        if (this.#container) return this.#container;

        const container = document.createElement("div");

        container.slot = CAPTCHA_SLOT;
        container.className = "ak-captcha-container";

        this.#container = container;

        return container;
    }

    //#endregion

    //#region Render

    protected renderBody() {
        if (this.error) {
            return html`<ak-empty-state icon="fa-times" .defaultLabel=${false}>
                <div>${msg("The CAPTCHA challenge failed to load.")}</div>
                <div slot="body">${AKFormErrors({ errors: [this.error] })}</div></ak-empty-state
            >`;
        }

        if (this.challenge?.interactive) {
            return html`
                <div
                    role="group"
                    aria-label=${msg("CAPTCHA challenge")}
                    class="ak-interactive-challenge"
                    data-ready=${this.widgetLoaded ? "ready" : "loading"}
                >
                    <slot name=${CAPTCHA_SLOT}></slot>
                </div>
            `;
        }

        return html`${akEmptyState({ loading: true }, { heading: msg("Verifying...") })}
            <slot name=${CAPTCHA_SLOT} class="ak-invisible-challenge"></slot>`;
    }

    protected renderMain() {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                ${FlowUserDetails({ challenge: this.challenge })} ${this.renderBody()}
            </form>
        </ak-flow-card>`;
    }

    protected render() {
        if (!this.challenge) {
            return this.embedded ? nothing : akEmptyState({ loading: true });
        }

        if (!this.embedded) {
            return this.renderMain();
        }

        return this.renderBody();
    }

    //#endregion

    //#region Lifecycle

    public override connectedCallback(): void {
        super.connectedCallback();

        // Lit doesn't re-run `updated` on reconnect, so a stage that was moved in the DOM
        // would otherwise stay empty until its next challenge.
        if (this.hasUpdated && this.challenge && !this.#loadedChallenge) {
            this.#loadedChallenge = this.challenge;
            this.#load();
        }
    }

    public disconnectedCallback(): void {
        this.#listenController.abort();

        this.#loadGeneration++;
        this.#loadedChallenge = null;
        this.#teardown();

        super.disconnectedCallback();
    }

    protected override updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        // Flows can show multiple CAPTCHA stages in sequence while reusing this element.
        // Only `challenge` changes, so the widget must be rebuilt here (not only on first
        // render) to avoid showing a solved widget from the previous stage. A new stage
        // always gets a new challenge object, even when provider and site key are the same.
        if (changedProperties.has("challenge") && this.challenge !== this.#loadedChallenge) {
            this.#loadedChallenge = this.challenge;
            this.#load();

            return;
        }

        if (
            changedProperties.has("activeTheme") &&
            changedProperties.get("activeTheme") &&
            this.activeController
        ) {
            // A rebuilt widget would be unsolved while its token has already been handed on.
            if (this.#solved) return;

            this.#logger.debug(`Theme changed to \`${this.activeTheme}\``);
            this.#load();

            return;
        }

        if (!changedProperties.has("refreshedAt") || !this.challenge) {
            return;
        }

        this.#logger.debug("Refresh triggered");

        this.#solved = false;

        this.activeController?.reset().catch((error: unknown) => {
            this.#logger.warn("Failed to reset challenge", error);
        });
    }

    #teardown() {
        if (this.activeController) {
            this.removeController(this.activeController);
            this.activeController.unmount();
            this.activeController = null;
        }

        // The container lives outside this element's subtree, so dropping the stage does
        // not take it with it.
        this.#frameObserver?.disconnect();
        this.#frameObserver = undefined;
        this.#container?.remove();
        this.#container = undefined;
        this.widgetLoaded = false;
    }

    //#endregion

    //#region Loading

    async #load(): Promise<void> {
        const generation = ++this.#loadGeneration;

        this.#teardown();
        this.#solved = false;
        this.error = null;

        const source = this.challenge?.jsUrl;

        if (!source || !URL.canParse(source)) {
            this.#logger.debug("No challenge URL, skipping load.");

            return;
        }

        const challengeURL = new URL(source);
        const resolution = CaptchaController.resolve(CaptchaStage.controllers, challengeURL);

        if (!resolution) {
            this.error = msg("Could not find a suitable CAPTCHA provider.");

            return;
        }

        const { Controller, matched } = resolution;

        if (matched === "global") {
            // Nothing about the URL identified a vendor, so the choice came from whichever
            // global is already on `window` — which may well have been installed by a
            // different stage. Worth saying out loud when a widget misbehaves.
            this.#logger.warn(
                `No provider matched \`${challengeURL.href}\`; falling back to the \`${Controller.globalName}\` global. ` +
                    `Proxied CAPTCHA script URLs can be mis-detected when several providers are in play.`,
            );
        }

        const controller = new Controller(this);

        try {
            await loadCaptchaScript({
                url: controller.prepareURL() ?? challengeURL,
                type: Controller.scriptType,
                isAvailable: () => Controller.isAvailable(),
            });

            // The challenge changed while the vendor script was in flight; whatever we
            // mount now would belong to a stage the user has already left.
            if (generation !== this.#loadGeneration) {
                this.#logger.debug("Stale load, discarding.");
                this.removeController(controller);

                return;
            }

            const host = documentTreeHost(this);

            if (!host) {
                this.#logger.debug("No document-tree host, skipping.");

                return;
            }

            // The container has to be attached before a provider renders into it — several
            // of them measure it on the spot.
            host.appendChild(this.container);

            // Frames are decorated by the controller that is about to mount, which is not
            // `activeController` yet — that is only assigned once mounting succeeds.
            this.#frameObserver?.disconnect();

            this.#frameObserver = observeFrames(this.container, (frame) =>
                controller.decorateFrame(frame),
            );

            if (this.challenge?.interactive) {
                await controller.mount(this.container);
            } else {
                await controller.execute(this.container);
            }

            // A newer load may have started while the provider rendered. Its teardown
            // couldn't reach this controller, which isn't active yet.
            if (generation !== this.#loadGeneration) {
                this.#logger.debug("Stale mount, discarding.");
                controller.unmount();
                this.removeController(controller);

                return;
            }

            this.activeController = controller;
            this.#logger.debug(`[${Controller.globalName}]: mounted`);
        } catch (error) {
            if (generation !== this.#loadGeneration) {
                this.removeController(controller);

                return;
            }

            this.#logger.warn(`[${Controller.globalName}]: failed to mount`, error);

            this.error = pluckErrorDetail(error, "Unspecified error");
            this.removeController(controller);

            return;
        }

        // Locale changes are only interesting once the widget is up; reacting earlier
        // would re-enter the load we are still inside.
        window.addEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener, {
            signal: this.#listenController.signal,
        });
    }

    #localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (!this.activeController) return;

        if (event.detail.status === "error") {
            this.#logger.debug("Error loading locale:", event.detail);

            return;
        }

        if (event.detail.status === "loading") return;

        // A rebuilt widget would be unsolved while its token has already been handed on.
        if (this.#solved) return;

        this.#logger.debug(`Locale changed to \`${event.detail.readyLocale}\``);

        // Providers take their language at render time, so the widget has to be rebuilt
        // rather than told about the change.
        this.#load();
    };

    //#endregion

    //#region Host callbacks

    public onWidgetLoad = (): void => {
        this.widgetLoaded = true;
        this.onLoad?.();
    };

    //#endregion
}

export default CaptchaStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha": CaptchaStage;
    }
}
