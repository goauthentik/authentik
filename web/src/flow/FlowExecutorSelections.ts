import "#flow/sources/apple/AppleLoginInit";
import "#flow/sources/plex/PlexLoginInit";
import "#flow/sources/telegram/TelegramLogin";
import "#flow/stages/FlowErrorStage";
import "#flow/stages/FlowFrameStage";
import "#flow/stages/RedirectStage";

import { isMatching, match, P } from "ts-pattern";

export const propVariants = ["standard", "challenge"] as const;
type PropVariant = (typeof propVariants)[number];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ComponentImport = () => Promise<any>;

// Any of these are valid variations, so you don't have to specify that this stage takes the
// "standard" set of props, or if the server-side stage token and the client-side component tag are
// the same you only need to specify one. Although the PropVariants and TagName are both strings on
// the wire, custom element tags always contain a dash and the PropVariants don't, making them
// easy to distinguish.
//
type BaseStage =
    | [token: string, tag: string, variant: PropVariant]
    | [token: string, variant: PropVariant]
    | [token: string, tag: string]
    | [token: string];

type RawStage =
    | BaseStage
    | [token: string, tag: string, variant: PropVariant, import: ComponentImport]
    | [token: string, variant: PropVariant, import: ComponentImport]
    | [token: string, tag: string, import: ComponentImport]
    | [token: string, import: ComponentImport];

type Stage = {
    tag: string;
    variant: PropVariant;
    importfn?: ComponentImport;
};

// Tables are allowed to go wide, just for readability. Sorting them alphabetically helps, too.
//
// prettier-ignore
const rawStages: RawStage[] = [
    ["ak-provider-iframe-logout", async () => await import("#flow/providers/IFrameLogoutStage")],
    ["ak-provider-oauth2-device-code", "ak-flow-provider-oauth2-code", async () => await import("#flow/providers/oauth2/DeviceCode")],
    ["ak-provider-oauth2-device-code-finish", "ak-flow-provider-oauth2-code-finish", async () => await import("#flow/providers/oauth2/DeviceCodeFinish")],
    ["ak-provider-saml-native-logout", async () => await import("#flow/providers/saml/NativeLogoutStage")],
    ["ak-source-oauth-apple", "ak-flow-source-oauth-apple"],
    ["ak-source-plex", "ak-flow-source-plex"],
    ["ak-source-telegram", "ak-flow-source-telegram"],
    ["ak-stage-access-denied", async () => await import("#flow/stages/access_denied/AccessDeniedStage")],
    ["ak-stage-authenticator-duo", async () => await import("#flow/stages/authenticator_duo/AuthenticatorDuoStage")],
    ["ak-stage-authenticator-email", async () => await import("#flow/stages/authenticator_email/AuthenticatorEmailStage")],
    ["ak-stage-authenticator-sms", async () => await import("#flow/stages/authenticator_sms/AuthenticatorSMSStage")],
    ["ak-stage-authenticator-static", async () => await import("#flow/stages/authenticator_static/AuthenticatorStaticStage")],
    ["ak-stage-authenticator-totp", async () => await import("#flow/stages/authenticator_totp/AuthenticatorTOTPStage")],
    ["ak-stage-authenticator-validate", async () => await import("#flow/stages/authenticator_validate/AuthenticatorValidateStage")],
    ["ak-stage-authenticator-webauthn"],
    ["ak-stage-autosubmit", async () => await import("#flow/stages/autosubmit/AutosubmitStage")],
    ["ak-stage-captcha", async () => await import("#flow/stages/captcha/CaptchaStage")],
    ["ak-stage-consent", async () => await import("#flow/stages/consent/ConsentStage")],
    ["ak-stage-dummy", async () => await import("#flow/stages/dummy/DummyStage")],
    ["ak-stage-email", async () => await import("#flow/stages/email/EmailStage")],
    ["ak-stage-endpoint-agent", "challenge", async () => await import("#flow/stages/endpoint/agent/EndpointAgentStage")],
    ["ak-stage-flow-error"],
    ["ak-stage-identification", async () => await import("#flow/stages/identification/IdentificationStage")],
    ["ak-stage-password", async () => await import("#flow/stages/password/PasswordStage")],
    ["ak-stage-prompt", async () => await import("#flow/stages/prompt/PromptStage")],
    ["ak-stage-session-end", async () => await import("#flow/providers/SessionEnd")],
    ["ak-stage-user-login", "challenge", async () => await import("#flow/stages/user_login/UserLoginStage")],
    ["xak-flow-redirect", "ak-stage-redirect"],
    ["xak-flow-frame", "challenge"],
];

const isImport = isMatching(P.when((x): x is ComponentImport => typeof x === "function"));

const PVariant = P.when(
    (x): x is PropVariant => typeof x === "string" && propVariants.includes(x as PropVariant),
);

// Don't have to type-check what you get from the tap.
const STANDARD = propVariants[0];

type InStage = [token: string, tag: string, variant: PropVariant];

export const stages: Map<string, Stage> = new Map(
    rawStages.map((rawstage: RawStage) => {
        // The RawStages table above is clear and lacks the repetition of the original, but it does
        // mean that doing all the pattern matching to normalize this to the format consumed by the
        // FlowExecutor looks a little hairy. Repetition, defaults, and optional values can be
        // ignored, making the table small and elegant, and this runs exactly once at start-time, so
        // its run-time cost is well worth the savings. The use of `.exhaustive()` at the bottom
        // guarantees that every variant specified in the `RawStage` type is handled.
        //
        // P.optional(PImport) does not work with tuples, but since it *is* optional and it *is* the
        // last thing when it's present, we lop it off for the purpose of checking the rest, so the
        // actual comparison table is for all the other variants, then put it back when we assemble
        // the map.  This eliminates half the variant checks.
        //
        const last = rawstage.at(-1);
        const importfn = isImport(last) ? last : undefined;
        const rest: BaseStage = (importfn ? rawstage.slice(0, -1) : rawstage) as BaseStage;

        // prettier-ignore
        const [token, tag, variant] = match<BaseStage, InStage>(rest)
            .with([P.string, P.string, PVariant], ([token, tag, variant]) => [token, tag, variant])
            .with([P.string, PVariant], ([token, variant]) => [token, token, variant])
            .with([P.string, P.string], ([token, tag]) => [token, tag, STANDARD])
            .with([P.string], ([token])=> [token, token, STANDARD])
            .exhaustive();

        return [token, { tag, variant, importfn }];
    }),
);
