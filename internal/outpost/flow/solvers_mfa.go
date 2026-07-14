package flow

import (
	"strings"
)

const CodePasswordSeparator = ";"

// Sets the secret answers for the flow executor for protocols that only support username/password
// according to used options
func (fe *FlowExecutor) SetSecrets(password string, mfaCodeBased bool) {
	if fe.Answers[StageAuthenticatorValidate] != "" || fe.Answers[StagePassword] != "" {
		return
	}
	fe.Answers[StagePassword] = password
	if !mfaCodeBased {
		// If code-based MFA is disabled StageAuthenticatorValidate answer is set to password.
		// This allows flows with a mfa stage only.
		fe.Answers[StageAuthenticatorValidate] = password
		return
	}
	// password doesn't contain the separator
	if !strings.Contains(password, CodePasswordSeparator) {
		return
	}
	// password ends with the separator, so it won't contain an answer
	if strings.HasSuffix(password, CodePasswordSeparator) {
		return
	}
	idx := strings.LastIndex(password, CodePasswordSeparator)
	authenticator := password[idx+1:]
	// Authenticator is either 6 / 8 digits (TOTP) or any length (static code)
	// and as a result we can't really validate whether what we've
	// extracted is a valid recovery code.
	fe.Answers[StagePassword] = password[:idx]
	fe.Answers[StageAuthenticatorValidate] = authenticator
}
