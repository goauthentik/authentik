import "@goauthentik/elements/messages/MessageContainer.js";
import "@goauthentik/flow/FlowExecutor.js";
// Statically import some stages to speed up load speed
import "@goauthentik/flow/stages/access_denied/AccessDeniedStage.js";
// Import webauthn-related stages to prevent issues on safari
// Which is overly sensitive to allowing things only in the context of a
// user interaction
import "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage.js";
import "@goauthentik/flow/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage.js";
import "@goauthentik/flow/stages/autosubmit/AutosubmitStage.js";
import "@goauthentik/flow/stages/captcha/CaptchaStage.js";
import "@goauthentik/flow/stages/identification/IdentificationStage.js";
import "@goauthentik/flow/stages/password/PasswordStage.js";

// end of stage import
