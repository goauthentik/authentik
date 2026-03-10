/**
 * @file Flow executor stage definitions.
 *
 * @remarks
 * The following imports must be imported statically, as they define web components that are used in stage definitions below.
 */

import "#flow/sources/apple/AppleLoginInit";
import "#flow/sources/plex/PlexLoginInit";
import "#flow/sources/telegram/TelegramLogin";
import "#flow/stages/FlowErrorStage";
import "#flow/stages/FlowFrameStage";
import "#flow/stages/RedirectStage";
import "#flow/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";

import type {
    FlowChallengeComponentName,
    PropVariant,
    StageModuleCallback,
} from "#flow/FlowExecutorStageFactory";

/**
 * An interface representing the metadata for a stage entry in the stage mapping registry.
 */
export interface StageEntry {
    stage: FlowChallengeComponentName;
    fetch?: StageModuleCallback;
    variant?: PropVariant;
    tag?: string;
}

/**
 * A mapping of server-side stage tokens to client-side custom element tags, along with the variant
 * of props they consume and an optional import callback for lazy-loading.
 *
 * @remarks
 * The different ways a stage can be associated with its server-side component are listed in the
 * type declaration above. The variants are meant to reduce the amount of information you have to
 * provide:
 *
 * - If the server-side component and the client-side tag are the same, only provide the component.
 * - Variants describe the attribute needs. There are only two variant: "standard" and "challenge."
 *   The "challenge" variant is for components that immediately issue redirects. "standard" is the
 *   default; you don't need to specify it.
 * - If the stage needs to be live immediately, import it above. Otherwise, provide an import
 *   function, following the examples already provided.
 *
 * Variants and Tags have a single strong differentiator: Tags refer to web components and so must
 * always have a dash, whereas variants are from a limited supply of names and do not have a dash.
 * The StageFactory will not get confused. If you get confused, the type-checker will explain it.
 *
 * The resolution of the web component tag name is: tag supplied, tag received with import, tag
 * derived from component name. THIS CAN FAIL: a preloaded stage with an incongruent and non- or
 * incorrectly-specified tag will result in a stage that cannot be rendered. Pre-loaded stages must
 * be tested carefully.
 */
// ,---.    |    |    ,   .              ,---.|                            |   |
// |---|,---|,---|    |\  |,---.. . .    `---.|--- ,---.,---.,---.,---.    |---|,---.,---.,---.
// |   ||   ||   |    | \ ||---'| | |        ||    ,---||   ||---'`---.    |   ||---'|    |---'
// `   '`---'`---'    `  `'`---'`-'-'    `---'`---'`---^`---|`---'`---'    `   '`---'`    `---'
//                                                      `---'

// prettier-ignore
export const StageEntries: readonly StageEntry[] = [
    {
        stage: "ak-provider-iframe-logout",
        fetch: () => import("#flow/providers/IFrameLogoutStage"),
    },
    {
        stage: "ak-provider-oauth2-device-code",
        fetch: () => import("#flow/providers/oauth2/DeviceCode"),
    },
    {
        stage: "ak-provider-oauth2-device-code-finish",
        fetch: () => import("#flow/providers/oauth2/DeviceCodeFinish"),
    },
    {
        stage: "ak-provider-saml-native-logout",
        fetch: () => import("#flow/providers/saml/NativeLogoutStage"),
    },
    {
        stage: "ak-source-oauth-apple",
        tag: "ak-flow-source-oauth-apple",
    },
    {
        stage: "ak-source-plex",
        tag: "ak-flow-source-plex",
    },
    {
        stage: "ak-source-telegram",
        tag: "ak-flow-source-telegram",
    },
    {
        stage: "ak-stage-access-denied",
        fetch: () => import("#flow/stages/access_denied/AccessDeniedStage"),
    },
    {
        stage: "ak-stage-authenticator-duo",
        fetch: () => import("#flow/stages/authenticator_duo/AuthenticatorDuoStage"),
    },
    {
        stage: "ak-stage-authenticator-email",
        fetch: () => import("#flow/stages/authenticator_email/AuthenticatorEmailStage"),
    },
    {
        stage: "ak-stage-authenticator-sms",
        fetch: () => import("#flow/stages/authenticator_sms/AuthenticatorSMSStage"),
    },
    {
        stage: "ak-stage-authenticator-static",
        fetch: () => import("#flow/stages/authenticator_static/AuthenticatorStaticStage"),
    },
    {
        stage: "ak-stage-authenticator-totp",
        fetch: () => import("#flow/stages/authenticator_totp/AuthenticatorTOTPStage"),
    },
    {
        stage: "ak-stage-authenticator-validate",
        fetch: () => import("#flow/stages/authenticator_validate/AuthenticatorValidateStage"),
    },
    {
        stage: "ak-stage-authenticator-webauthn"
    },
    {
        stage: "ak-stage-autosubmit",
        fetch: () => import("#flow/stages/autosubmit/AutosubmitStage"),
    },
    {
        stage: "ak-stage-captcha",
        fetch: () => import("#flow/stages/captcha/CaptchaStage"),
    },
    {
        stage: "ak-stage-consent",
        fetch: () => import("#flow/stages/consent/ConsentStage"),
    },
    {
        stage: "ak-stage-dummy",
        fetch: () => import("#flow/stages/dummy/DummyStage"),
    },
    {
        stage: "ak-stage-email",
        fetch: () => import("#flow/stages/email/EmailStage"),
    },
    {
        stage: "ak-stage-endpoint-agent",
        fetch: () => import("#flow/stages/endpoint/agent/EndpointAgentStage"),
        variant: "challenge",
    },
    {
        stage: "ak-stage-flow-error"
    },
    {
        stage: "ak-stage-identification",
        fetch: () => import("#flow/stages/identification/IdentificationStage"),
    },
    {
        stage: "ak-stage-password",
        fetch: () => import("#flow/stages/password/PasswordStage"),
    },
    {
        stage: "ak-stage-prompt",
        fetch: () => import("#flow/stages/prompt/PromptStage"),
    },
    {
        stage: "ak-stage-session-end",
        fetch: () => import("#flow/providers/SessionEnd"),
    },
    {
        stage: "ak-stage-user-login",
        fetch: () => import("#flow/stages/user_login/UserLoginStage"),
        variant: "challenge",
    },
    {
        stage: "xak-flow-frame",
        variant: "challenge"
    },
    {
        stage: "xak-flow-redirect",
        tag: "ak-stage-redirect",
    },
];

export default StageEntries;
