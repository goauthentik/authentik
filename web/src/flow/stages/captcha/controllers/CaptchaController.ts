import type { ResolvedUITheme } from "#common/theme";

import { ErrorProp } from "#components/ak-field-errors";

import { ConsoleLogger, Logger } from "#logger/browser";

import { CaptchaChallenge } from "@goauthentik/api";

import { ReactiveController, ReactiveControllerHost, TemplateResult } from "lit";
import { Ref } from "lit/directives/ref.js";

/**
 * Mapping of captcha provider names to their respective JS API global.
 */
export const CaptchaProvider = {
    reCAPTCHA: "grecaptcha",
    hCaptcha: "hcaptcha",
    Turnstile: "turnstile",
} as const satisfies Record<string, string>;

export abstract class CaptchaController implements ReactiveController {
    /**
     * The runtime global name of this Captcha provider, e.g. `grecaptcha`.
     */
    public static readonly globalName: string = "";

    public get globalName(): string {
        return (this.constructor as typeof CaptchaController).globalName;
    }

    /**
     * A prefix for log messages from this controller.
     */
    protected static logPrefix = "controller";

    /**
     * Given a source of {@linkcode CaptchaControllerConstructor}s, return those
     * whose global is present in `window`.
     */
    public static discover(
        controllerConstructors: Iterable<CaptchaControllerConstructor>,
    ): Array<CaptchaControllerConstructor | undefined> {
        return Array.from(controllerConstructors).filter((Controller) => {
            // Can we find the global for this captcha provider?
            return Object.hasOwn(window, Controller.globalName);
        });
    }

    public hostConnected(): void {
        this.logger.debug("Host connected.");
    }

    public hostDisconnected(): void {
        this.logger.debug("Host disconnected.");
    }

    /**
     * Log a debug message with the controller's prefix.
     */
    protected readonly logger: Logger;

    public readonly host: CaptchaHandlerHost;

    /**
     * A callable that returns the interactive captcha element.
     */
    public abstract interactive: () => TemplateResult;

    /**
     * A callable that refreshes the interactive captcha element.
     */
    public abstract refreshInteractive: () => Promise<void>;
    /**
     * A callable that executes a non-interactive captcha challenge.
     */

    public abstract execute: () => Promise<void>;

    /**
     * A callable that refreshes a non-interactive captcha challenge.
     */
    public abstract refresh: () => Promise<void>;

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
} & (new (host: CaptchaHandlerHost) => CaptchaController);

export interface CaptchaHandlerHost extends ReactiveControllerHost {
    captchaDocumentContainer: HTMLElement;
    iframeRef: Ref<HTMLIFrameElement>;
    activeLanguageTag: string;
    activeTheme: ResolvedUITheme;
    challenge: CaptchaChallenge | null;
    error: ErrorProp | null;
    onTokenChange(token: string): void;
}
