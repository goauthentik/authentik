import type { ResolvedUITheme } from "#common/theme";

import { ErrorProp } from "#components/ak-field-errors";

import { CaptchaVendor, matchesVendorURL } from "#flow/stages/captcha/shared";

import { ConsoleLogger, Logger } from "#logger/browser";

import { CaptchaChallenge } from "@goauthentik/api";

import { ReactiveController, ReactiveControllerHost } from "lit";

/**
 * The result of resolving a challenge URL to a controller.
 */
export interface CaptchaResolution {
    Controller: CaptchaControllerConstructor;
    matched: "url" | "global";
}

export abstract class CaptchaController implements ReactiveController {
    /**
     * The vendor this controller drives.
     */
    public static readonly vendor: CaptchaVendor | null = null;

    /**
     * The runtime global name of this Captcha provider, e.g. `grecaptcha`.
     */
    public static readonly globalName: string = "";

    public get globalName(): string {
        return (this.constructor as typeof CaptchaController).globalName;
    }

    public static readonly scriptType: "classic" | "module" = "classic";

    public get scriptType(): "classic" | "module" {
        return (this.constructor as typeof CaptchaController).scriptType;
    }

    public static isAvailable(): boolean {
        return Object.hasOwn(window, this.globalName);
    }

    /**
     * Whether this controller handles the given challenge script URL.
     *
     * This is the primary selection mechanism — see {@linkcode CaptchaController.resolve}.
     */
    public static matchesURL(url: URL): boolean {
        return this.vendor ? matchesVendorURL(this.vendor, url) : false;
    }

    /**
     * A prefix for log messages from this controller.
     */
    protected static logPrefix = "controller";

    /**
     * Resolve the controller responsible for a given challenge script URL.
     *
     * @remarks
     *
     * Selection is by URL, not by which globals happen to be on `window`.
     *
     * Every provider installs a global with a fixed name (`grecaptcha`, `hcaptcha`,
     * `turnstile`), and those globals outlive the stage that loaded them: scripts are
     * appended to `document.head` and never removed, so a flow with an hCaptcha
     * identification stage followed by a Turnstile captcha stage ends up with both
     * globals present at once. Picking by global therefore returns whichever vendor
     * happens to sort first, not the one this challenge asked for — the widget renders
     * against the wrong site key and the token fails server-side validation.
     *
     * Matching the URL the server actually handed us removes the ambiguity, which is
     * what lets several vendors coexist in one document without an iframe per widget.
     *
     * Falling back to global discovery covers self-hosted and reverse-proxied script
     * URLs, which no host pattern can anticipate. That path is ambiguous by nature, so
     * the caller is told which mechanism was used.
     */
    public static resolve(
        controllerConstructors: Iterable<CaptchaControllerConstructor>,
        url: URL,
    ): CaptchaResolution | null {
        const controllers = Array.from(controllerConstructors);

        const byURL = controllers.find((Controller) => Controller.matchesURL(url));

        if (byURL) return { Controller: byURL, matched: "url" };

        const byGlobal = controllers.find((Controller) => Controller.isAvailable());

        if (byGlobal) return { Controller: byGlobal, matched: "global" };

        return null;
    }

    public hostConnected(): void {
        this.logger.debug("Host connected.");
    }

    public hostDisconnected(): void {
        this.unmount();
        this.logger.debug("Host disconnected.");
    }

    /**
     * Log a debug message with the controller's prefix.
     */
    protected readonly logger: Logger;

    public readonly host: CaptchaHandlerHost;

    /**
     * Render the provider's interactive widget into `container`.
     *
     * The container is a light-DOM element owned by the stage. Providers render their
     * own nested iframes into it and size themselves; the stage does not measure or
     * reposition anything.
     */
    public abstract mount(container: HTMLElement): Promise<void>;

    /**
     * Execute a non-interactive ("invisible") challenge.
     */
    public abstract execute(container: HTMLElement): Promise<void>;

    /**
     * Discard the current token and present a fresh challenge.
     */
    public abstract reset(): Promise<void>;

    /**
     * Adjust a frame the provider has just added to the container.
     *
     * Called from the stage's mutation observer for every iframe that appears under the
     * container, after the stage has pinned the frame to its declared size. The default
     * leaves the frame alone.
     */
    public decorateFrame(_frame: HTMLIFrameElement): void {
        // Optional for providers whose frames need no adjustment.
    }

    /**
     * Tear down any provider state. Must be safe to call when nothing was mounted.
     */
    public unmount(): void {
        // Optional for providers with no teardown of their own.
    }

    public prepareURL(): URL | null {
        const source = this.host.challenge?.jsUrl;

        return source && URL.canParse(source) ? new URL(source) : null;
    }

    public constructor(host: CaptchaHandlerHost) {
        const { logPrefix } = this.constructor as typeof CaptchaController;

        this.logger = ConsoleLogger.prefix(`controller/${logPrefix}`);
        this.host = host;
        this.host.addController(this);
    }
}

export type CaptchaControllerConstructor = {
    globalName: string;
    scriptType: "classic" | "module";
    isAvailable: () => boolean;
    matchesURL: (url: URL) => boolean;
} & (new (host: CaptchaHandlerHost) => CaptchaController);

export interface CaptchaHandlerHost extends ReactiveControllerHost {
    activeLanguageTag: string;
    activeTheme: ResolvedUITheme;
    challenge: CaptchaChallenge | null;
    error: ErrorProp | null;
    onTokenChange(token: string): void;
    /**
     * Called by a controller once its widget is visible and sized.
     */
    onWidgetLoad(): void;
}
