package flow

import (
	"regexp"
	"strconv"
	"strings"
)

const CodePasswordSeparator = ";"

var alphaNum = regexp.MustCompile(`^[a-zA-Z0-9]*$`)

// CheckPasswordInlineMFA For protocols that only support username/password, check if the password
// contains the TOTP code
func (fe *FlowExecutor) CheckPasswordInlineMFA() {
	password := fe.Answers[StagePassword]
	// We already have an authenticator answer
	if fe.Answers[StageAuthenticatorValidate] != "" {
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
	// Authenticator is either 6 chars (totp code) or 8 chars (long totp or static)
	if len(authenticator) == 6 {
		// authenticator answer isn't purely numerical, so won't be value
		if _, err := strconv.Atoi(authenticator); err != nil {
			return
		}
	} else if len(authenticator) == 8 {
		// 8 chars can be a long totp or static token, so it needs to be alphanumerical
		if !alphaNum.MatchString(authenticator) {
			return
		}
	} else {
		// Any other length, doesn't contain an answer
		return
	}
	fe.Answers[StagePassword] = password[:idx]
	fe.Answers[StageAuthenticatorValidate] = authenticator
}
