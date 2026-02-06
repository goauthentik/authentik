import "#flow/sources/apple/AppleLoginInit";
import "#flow/sources/plex/PlexLoginInit";
import "#flow/sources/telegram/TelegramLogin";
import "#flow/stages/FlowErrorStage";
import "#flow/stages/FlowFrameStage";
import "#flow/stages/RedirectStage";

import type { FlowChallengeComponentName, PropVariant, StageModuleCallback } from "./FlowExecutorStageFactory";

// prettier-ignore
type StageEntry =
    | [token: FlowChallengeComponentName, tag: string, variant: PropVariant, import?: StageModuleCallback]
    | [token: FlowChallengeComponentName, variant: PropVariant, import?: StageModuleCallback]
    | [token: FlowChallengeComponentName, tag: string, import?: StageModuleCallback]
    | [token: FlowChallengeComponentName, import?: StageModuleCallback];

type StageEntries = StageEntry[];

// ,---.    |    |    ,   .              ,---.|                            |   |
// |---|,---|,---|    |\  |,---.. . .    `---.|--- ,---.,---.,---.,---.    |---|,---.,---.,---.
// |   ||   ||   |    | \ ||---'| | |        ||    ,---||   ||---'`---.    |   ||---'|    |---'
// `   '`---'`---'    `  `'`---'`-'-'    `---'`---'`---^`---|`---'`---'    `   '`---'`    `---'
//                                                      `---'
// @remarks
// The different ways a stage can be associated with its server-side component are listed in the
// type declaration above. The variants are meant to reduce the amount of information you have to
// provide:
//
// - If the server-side component and the client-side tag are the same, only provide the component.
// - Variants describe the attribute needs. There are only two variant: "standard" and "challenge."
//   The "challenge" variant is for components that immediately issue redirects. "standard" is the
//   default; you don't need to specify it.
// - If the stage needs to be live immediately, import it above. Otherwise, provide an import
//   function, following the examples already provided.
//
// Variants and Tags have a single strong differentiator: Tags refer to web components and so must
// always have a dash, whereas wariants are from a limited supply of names and do not have a dash.
// The StageFactory will not get confused. If you get confused, the type-checker will explain it.
//
// The resolution of the web component tag name is: tag supplied, tag received with import, tag
// derived from component name. THIS CAN FAIL: a preloaded stage with an incongruent and non- or
// incorrectly-specified tag will result in a stage that cannot be rendered. Pre-loaded stages must
// be tested carefully.

// prettier-ignore
export const StageModules: StageEntries = [
    ["ak-provider-iframe-logout", () => import("#flow/providers/IFrameLogoutStage")],
    ["ak-provider-oauth2-device-code-finish", () => import("#flow/providers/oauth2/DeviceCodeFinish")],
    ["ak-provider-oauth2-device-code", () => import("#flow/providers/oauth2/DeviceCode")],
    ["ak-provider-saml-native-logout", () => import("#flow/providers/saml/NativeLogoutStage")],

    ["ak-stage-access-denied", () => import("#flow/stages/access_denied/AccessDeniedStage")],
    ["ak-stage-authenticator-duo", () => import("#flow/stages/authenticator_duo/AuthenticatorDuoStage")],
    ["ak-stage-authenticator-email", () => import("#flow/stages/authenticator_email/AuthenticatorEmailStage")],
    ["ak-stage-authenticator-sms", () => import("#flow/stages/authenticator_sms/AuthenticatorSMSStage")],
    ["ak-stage-authenticator-static", () => import("#flow/stages/authenticator_static/AuthenticatorStaticStage")],
    ["ak-stage-authenticator-totp", () => import("#flow/stages/authenticator_totp/AuthenticatorTOTPStage")],
    ["ak-stage-authenticator-validate", () => import("#flow/stages/authenticator_validate/AuthenticatorValidateStage")],
    ["ak-stage-autosubmit", () => import("#flow/stages/autosubmit/AutosubmitStage")],
    ["ak-stage-captcha", () => import("#flow/stages/captcha/CaptchaStage")],
    ["ak-stage-consent", () => import("#flow/stages/consent/ConsentStage")],
    ["ak-stage-dummy", () => import("#flow/stages/dummy/DummyStage")],
    ["ak-stage-email", () => import("#flow/stages/email/EmailStage")],
    ["ak-stage-identification", () => import("#flow/stages/identification/IdentificationStage")],
    ["ak-stage-password", () => import("#flow/stages/password/PasswordStage")],
    ["ak-stage-prompt", () => import("#flow/stages/prompt/PromptStage")],
    ["ak-stage-session-end", () => import("#flow/providers/SessionEnd")],

    ["ak-stage-endpoint-agent", "challenge", () => import("#flow/stages/endpoint/agent/EndpointAgentStage")],
    ["ak-stage-user-login", "challenge", () => import("#flow/stages/user_login/UserLoginStage")],

    ["ak-source-oauth-apple", "ak-flow-source-oauth-apple"],
    ["ak-stage-authenticator-webauthn"],
    ["ak-stage-flow-error"],

    ["ak-source-plex", "ak-flow-source-plex"],
    ["ak-source-telegram", "ak-flow-source-telegram"],

    ["xak-flow-frame", "challenge"],
    ["xak-flow-redirect", "ak-stage-redirect"],
]

// You don't see this imported to `FlowExecutor` because what the Executor actually uses is produced
// by the builder. This is just an easy-to-read place to store each stage's server-side component
// name and the metadata needed to associate it with the client-side operation.

export default StageModules;
