import "#elements/messages/MessageContainer";
import "#flow/FlowExecutor";
// Statically import some stages to speed up load speed
import "#flow/stages/access_denied/AccessDeniedStage";
// Import webauthn-related stages to prevent issues on safari
// Which is overly sensitive to allowing things only in the context of a
// user interaction
import "#flow/stages/authenticator_validate/AuthenticatorValidateStage";
import "#flow/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import "#flow/stages/autosubmit/AutosubmitStage";
import "#flow/stages/captcha/CaptchaStage";
import "#flow/stages/identification/IdentificationStage";
import "#flow/stages/password/PasswordStage";

// end of stage import

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}
