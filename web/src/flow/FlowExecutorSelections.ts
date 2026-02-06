import "#flow/sources/apple/AppleLoginInit";
import "#flow/sources/plex/PlexLoginInit";
import "#flow/sources/telegram/TelegramLogin";
import "#flow/stages/FlowErrorStage";
import "#flow/stages/FlowFrameStage";
import "#flow/stages/RedirectStage";

import type { UnwrapSet } from "#common/sets";

import type { FlowChallengeComponentName, StageModuleCallback } from "#flow/types";

export const propVariants = new Set(["standard", "challenge", "inspect"] as const);
type PropVariant = UnwrapSet<typeof propVariants>;

/**
 * @remarks
 * Any of these are valid variations, so you don't have to specify that this stage takes the
 * "standard" set of props, or if the server-side stage token and the client-side component tag are
 * the same you only need to specify one. Although the PropVariants and TagName are both strings on
 * the wire, custom element tags always contain a dash and the PropVariants don't, making them
 * easy to distinguish.
 */
type StageEntry =
    | StageModuleCallback
    | [PropVariant?, tagName?: string]
    | [PropVariant, StageModuleCallback]
    | null;

// Tables are allowed to go wide, just for readability. Sorting them alphabetically helps, too.
// prettier-ignore
const StageModuleRecord: Record<FlowChallengeComponentName, StageEntry> = {
    "ak-provider-iframe-logout": () => import("#flow/providers/IFrameLogoutStage"),
    "ak-provider-oauth2-device-code-finish": () => import("#flow/providers/oauth2/DeviceCodeFinish"),
    "ak-provider-oauth2-device-code": () => import("#flow/providers/oauth2/DeviceCode"),
    "ak-provider-saml-native-logout": () => import("#flow/providers/saml/NativeLogoutStage"),

    "ak-stage-access-denied": () => import("#flow/stages/access_denied/AccessDeniedStage"),
    "ak-stage-authenticator-duo": () => import("#flow/stages/authenticator_duo/AuthenticatorDuoStage"),
    "ak-stage-authenticator-email": () => import("#flow/stages/authenticator_email/AuthenticatorEmailStage"),
    "ak-stage-authenticator-sms": () => import("#flow/stages/authenticator_sms/AuthenticatorSMSStage"),
    "ak-stage-authenticator-static": () => import("#flow/stages/authenticator_static/AuthenticatorStaticStage"),
    "ak-stage-authenticator-totp": () => import("#flow/stages/authenticator_totp/AuthenticatorTOTPStage"),
    "ak-stage-authenticator-validate": () => import("#flow/stages/authenticator_validate/AuthenticatorValidateStage"),
    "ak-stage-autosubmit": () => import("#flow/stages/autosubmit/AutosubmitStage"),
    "ak-stage-captcha": () => import("#flow/stages/captcha/CaptchaStage"),
    "ak-stage-consent": () => import("#flow/stages/consent/ConsentStage"),
    "ak-stage-dummy": () => import("#flow/stages/dummy/DummyStage"),
    "ak-stage-email": () => import("#flow/stages/email/EmailStage"),
    "ak-stage-identification": () => import("#flow/stages/identification/IdentificationStage"),
    "ak-stage-password": () => import("#flow/stages/password/PasswordStage"),
    "ak-stage-prompt": () => import("#flow/stages/prompt/PromptStage"),
    "ak-stage-session-end": () => import("#flow/providers/SessionEnd"),

    "ak-stage-endpoint-agent": ["challenge", () => import("#flow/stages/endpoint/agent/EndpointAgentStage")],
    "ak-stage-user-login": ["challenge", () => import("#flow/stages/user_login/UserLoginStage")],

    "ak-source-oauth-apple": ["standard", "ak-flow-source-oauth-apple"],
    "ak-stage-authenticator-webauthn": [],
    "ak-stage-flow-error": [],

    "ak-source-plex": ["standard", "ak-flow-source-plex"],
    "ak-source-telegram": ["standard", "ak-flow-source-telegram"],

    "xak-flow-frame": ["challenge"],
    "xak-flow-redirect": ["inspect", "ak-stage-redirect"],
    "xak-flow-shell": null,
}

type StageMapping =
    | {
          variant: PropVariant;
          tag: string;
          importCallback: null;
      }
    | {
          variant: PropVariant;
          tag: null;
          importCallback: StageModuleCallback;
      };

/**
 * A mapping of server-side stage tokens to client-side custom element tags, along with the variant of props they consume and an optional import callback for lazy-loading.
 *
 * @remarks
 * This is the actual table of stages consumed by the FlowExecutor.
 * It is generated from the more concise `StageModuleRecord` above, which is easier to read and maintain.
 * The `StageModuleRecord` allows for specifying just the token, or the token and variant,
 * or the token and tag, or all three, and it can also include an import callback if the stage should be lazy-loaded.
 * The code below normalizes all of these possibilities into a consistent format that the FlowExecutor can use.
 */
export const StageMappings: ReadonlyMap<FlowChallengeComponentName, StageMapping | null> = new Map(
    Object.entries(StageModuleRecord).map(
        (foo): [FlowChallengeComponentName, StageMapping | null] => {
            const [token, entry] = foo as [FlowChallengeComponentName, StageEntry | null];

            if (entry === null) {
                return [token, null];
            }

            if (typeof entry === "function") {
                return [token, { tag: null, variant: "standard", importCallback: entry }];
            }

            const [variant = "standard", maybeTagOrImport = token] = entry;

            if (typeof maybeTagOrImport === "function") {
                return [token, { tag: null, variant, importCallback: maybeTagOrImport }];
            }

            return [token, { tag: maybeTagOrImport, variant, importCallback: null }];
        },
    ),
);

/**
 * A cache for storing the resolved custom element tag names for stage mappings that require lazy-loading.
 */
const StageMappingTagNameCache = new WeakMap<StageMapping, string>();

/**
 * Given a stage mapping, returns the custom element tag name for that stage, loading the module if necessary.
 *
 * @param stageMapping The mapping for the stage, which may include a direct tag name or an import callback for lazy-loading.
 * @returns The custom element tag name for the stage.
 * @throws {TypeError} If the module fails to load or does not define a custom element.
 */
export async function readStageModuleTag(stageMapping: StageMapping): Promise<string> {
    if (stageMapping.importCallback === null) {
        return stageMapping.tag;
    }

    if (StageMappingTagNameCache.has(stageMapping)) {
        return StageMappingTagNameCache.get(stageMapping)!;
    }

    const module = await stageMapping.importCallback();
    const StageConstructor = module.default;
    const tag = window.customElements.getName(StageConstructor);

    if (!tag) {
        // eslint-disable-next-line no-console
        console.trace(
            `Failed to load stage module: no custom element found in module`,
            stageMapping,
        );
        throw new TypeError("Failed to load stage module: no custom element found");
    }

    StageMappingTagNameCache.set(stageMapping, tag);

    return tag;
}
