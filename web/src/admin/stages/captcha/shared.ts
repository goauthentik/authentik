import { CaptchaStage, CaptchaStageRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";

export type CaptchaRequestContentType = "application/x-www-form-urlencoded" | "application/json";

export const CAPTCHA_REQUEST_CONTENT_TYPES = [
    {
        value: "application/x-www-form-urlencoded",
        formatDisplayName: () =>
            msg("Form encoded", {
                id: "captcha.request-content-type.form",
            }),
    },
    {
        value: "application/json",
        formatDisplayName: () =>
            msg("JSON", {
                id: "captcha.request-content-type.json",
            }),
    },
] as const satisfies {
    value: CaptchaRequestContentType;
    formatDisplayName: () => string;
}[];

export const CaptchaProviderKeys = [
    "recaptcha_v2",
    "recaptcha_v3",
    "recaptcha_enterprise",
    "hcaptcha",
    "turnstile",
    "cap",
    "custom",
] as const satisfies string[];

export type CaptchaProviderKey = (typeof CaptchaProviderKeys)[number];

export interface CaptchaProviderPreset {
    formatDisplayName: () => string;
    formatDescription?: () => string;
    jsUrl: string;
    apiUrl: string;
    requestContentType: CaptchaRequestContentType;
    interactive: boolean;
    supportsScore: boolean;
    score?: { min: number; max: number };
    formatAPISource?: () => string;
    keyURL?: string;
}

/**
 * Provider presets for common CAPTCHA services.
 * Each preset contains default URLs, settings, and help text with links to provider dashboards.
 * When a provider is selected, these values auto-fill the form but remain editable.
 */
export const CAPTCHA_PROVIDERS = {
    recaptcha_v2: {
        formatDisplayName: () =>
            msg("Google reCAPTCHA v2", {
                id: "captcha.providers.recaptcha-v2",
            }),
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        requestContentType: "application/x-www-form-urlencoded",
        interactive: true,
        supportsScore: false,
        formatAPISource: () =>
            msg("reCAPTCHA admin console", {
                id: "captcha.providers.recaptcha.admin-console",
            }),
        keyURL: "https://www.google.com/recaptcha/admin",
    },
    recaptcha_v3: {
        formatDisplayName: () =>
            msg("Google reCAPTCHA v3", {
                id: "captcha.providers.recaptcha-v3",
            }),
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        requestContentType: "application/x-www-form-urlencoded",
        interactive: false,
        supportsScore: true,
        score: { min: 0.5, max: 1.0 },
        formatAPISource: () =>
            msg("reCAPTCHA admin console", {
                id: "captcha.providers.recaptcha.api-key-source",
            }),
        keyURL: "https://www.google.com/recaptcha/admin",
    },
    recaptcha_enterprise: {
        formatDisplayName: () =>
            msg("Google reCAPTCHA Enterprise", {
                id: "captcha.providers.recaptcha-enterprise",
            }),
        jsUrl: "https://www.recaptcha.net/recaptcha/enterprise.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        requestContentType: "application/x-www-form-urlencoded",
        interactive: false,
        supportsScore: true,
        score: { min: 0.5, max: 1.0 },
        formatAPISource: () =>
            msg("Google Cloud Console", {
                id: "captcha.providers.recaptcha-enterprise.api-key-source",
            }),
        keyURL: "https://cloud.google.com/recaptcha-enterprise",
    },
    hcaptcha: {
        formatDisplayName: () =>
            msg("hCaptcha", {
                id: "captcha.providers.hcaptcha",
            }),
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        apiUrl: "https://api.hcaptcha.com/siteverify",
        requestContentType: "application/x-www-form-urlencoded",
        interactive: true,
        supportsScore: true,
        score: { min: 0.0, max: 0.5 },
        formatAPISource: () =>
            msg("hCaptcha dashboard", {
                id: "captcha.providers.hcaptcha.api-key-source",
            }),
        keyURL: "https://dashboard.hcaptcha.com",
    },
    turnstile: {
        formatDisplayName: () =>
            msg("Cloudflare Turnstile", {
                id: "captcha.providers.turnstile",
            }),
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        apiUrl: "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        requestContentType: "application/x-www-form-urlencoded",
        interactive: true,
        supportsScore: false,
        formatAPISource: () =>
            msg("Cloudflare dashboard", {
                id: "captcha.providers.turnstile.api-key-source",
            }),
        keyURL: "https://dash.cloudflare.com",
    },
    cap: {
        formatDisplayName: () =>
            msg("Cap", {
                id: "captcha.providers.cap",
            }),
        formatDescription: () =>
            msg("Cap is a self-hostable CAPTCHA server that uses proof-of-work challenges.", {
                id: "captcha.providers.cap.description",
            }),
        jsUrl: "https://cap.example.com/assets/widget.js",
        apiUrl: "https://cap.example.com/site-key/siteverify",
        requestContentType: "application/json",
        interactive: true,
        supportsScore: false,
        formatAPISource: () =>
            msg("Cap documentation", {
                id: "captcha.providers.cap.setup-guide",
            }),
        keyURL: "https://trycap.dev/guide/",
    },
    custom: {
        formatDisplayName: () =>
            msg("Custom", {
                id: "captcha.providers.custom",
            }),
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        requestContentType: "application/x-www-form-urlencoded",
        interactive: false,
        supportsScore: true,
        score: { min: 0.5, max: 1.0 },
    },
} as const satisfies Record<CaptchaProviderKey, CaptchaProviderPreset>;

export function deriveCapSiteVerifyURL(endpoint: string): string | null {
    const trimmedEndpoint = endpoint.trim();

    if (!URL.canParse(trimmedEndpoint)) {
        return null;
    }

    const endpointURL = new URL(trimmedEndpoint);
    const normalizedEndpoint = endpointURL.href.endsWith("/")
        ? endpointURL.href
        : `${endpointURL.href}/`;

    return new URL("siteverify", normalizedEndpoint).toString();
}

/**
 * Detect which provider preset matches the given {@linkcode CaptchaStage} instance.
 * This allows the form to show the correct provider in the dropdown when editing
 * an existing CAPTCHA stage. Falls back to "custom" if no match is found.
 */
function isCapWidgetURL(jsUrl?: string | null): boolean {
    if (!jsUrl || !URL.canParse(jsUrl)) {
        return false;
    }

    const { pathname } = new URL(jsUrl);
    return pathname.includes("cap-widget") || pathname.endsWith("/assets/widget.js");
}

export function detectProviderFromInstance(stage?: CaptchaStage | null): CaptchaProviderKey {
    if (!stage) return "custom";

    for (const key of CaptchaProviderKeys) {
        const preset = CAPTCHA_PROVIDERS[key];

        if (
            key === "cap" &&
            isCapWidgetURL(stage.jsUrl) &&
            stage.requestContentType === preset.requestContentType
        ) {
            return key;
        }
      
        const hasScore =
            stage.scoreMinThreshold !== undefined && stage.scoreMaxThreshold !== undefined;

        const scoreValueMatchesPreset = preset.supportsScore === hasScore;
      
        if (
            stage.jsUrl === preset.jsUrl &&
            stage.apiUrl === preset.apiUrl &&
            stage.interactive === preset.interactive &&
            scoreValueMatchesPreset
        ) {
            return key;
        }
    }

    return "custom";
}

/**
 * Get the form values to display, with clear precedence:
 * 1. If editing an existing instance, use instance values
 * 2. Otherwise, use the current preset defaults
 */
export function pluckFormValues(
    instance?: CaptchaStage | null,
    preset: CaptchaProviderPreset = CAPTCHA_PROVIDERS.custom,
): Omit<CaptchaStageRequest, "name" | "publicKey" | "privateKey"> {
    if (instance) {
        return {
            jsUrl: instance.jsUrl,
            apiUrl: instance.apiUrl,
            requestContentType: instance.requestContentType,
            interactive: instance.interactive,
            scoreMinThreshold: instance.scoreMinThreshold,
            scoreMaxThreshold: instance.scoreMaxThreshold,
            errorOnInvalidScore: instance.errorOnInvalidScore ?? true,
        };
    }

    return {
        jsUrl: preset.jsUrl,
        apiUrl: preset.apiUrl,
        requestContentType: preset.requestContentType,
        interactive: preset.interactive,
        scoreMinThreshold: preset.score?.min ?? 0.5,
        scoreMaxThreshold: preset.score?.max ?? 1.0,
        errorOnInvalidScore: true,
    };
}
