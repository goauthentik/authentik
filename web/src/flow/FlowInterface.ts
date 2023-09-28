import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/flow/FlowExecutor";
// Statically import some stages to speed up load speed
import "@goauthentik/flow/stages/access_denied/AccessDeniedStage";
// Import webauthn-related stages to prevent issues on safari
// Which is overly sensitive to allowing things only in the context of a
// user interaction
import "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage";
import "@goauthentik/flow/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import "@goauthentik/flow/stages/autosubmit/AutosubmitStage";
import "@goauthentik/flow/stages/captcha/CaptchaStage";
import "@goauthentik/flow/stages/identification/IdentificationStage";
import "@goauthentik/flow/stages/password/PasswordStage";

// end of stage import
