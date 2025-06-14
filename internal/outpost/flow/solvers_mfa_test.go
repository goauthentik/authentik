package flow_test

import (
	"context"
	"encoding/base64"
	"fmt"
	"strconv"
	"testing"

	"github.com/gorilla/securecookie"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/flow"
)

func testSecret() string {
	return base64.RawURLEncoding.EncodeToString(securecookie.GenerateRandomKey(32))
}

func TestFlowExecutor_SetSecrets_Plain(t *testing.T) {
	fe := flow.NewFlowExecutor(context.TODO(), "", api.NewConfiguration(), logrus.Fields{})
	pw := testSecret()
	fe.SetSecrets(pw, false)
	assert.Equal(t, pw, fe.Answers[flow.StagePassword])
	assert.Equal(t, pw, fe.Answers[flow.StageAuthenticatorValidate])
}

func TestFlowExecutor_SetSecrets_TOTP_6(t *testing.T) {
	fe := flow.NewFlowExecutor(context.TODO(), "", api.NewConfiguration(), logrus.Fields{})
	pw := testSecret()
	totp := 123456
	formatted := fmt.Sprintf("%s%s%d", pw, flow.CodePasswordSeparator, totp)
	fe.SetSecrets(formatted, true)
	assert.Equal(t, pw, fe.Answers[flow.StagePassword])
	assert.Equal(t, strconv.Itoa(totp), fe.Answers[flow.StageAuthenticatorValidate])
}

func TestFlowExecutor_SetSecrets_TOTP_8(t *testing.T) {
	fe := flow.NewFlowExecutor(context.TODO(), "", api.NewConfiguration(), logrus.Fields{})
	pw := testSecret()
	totp := 12345678
	formatted := fmt.Sprintf("%s%s%d", pw, flow.CodePasswordSeparator, totp)
	fe.SetSecrets(formatted, true)
	assert.Equal(t, pw, fe.Answers[flow.StagePassword])
	assert.Equal(t, strconv.Itoa(totp), fe.Answers[flow.StageAuthenticatorValidate])
}

func TestFlowExecutor_SetSecrets_TOTP_TooLong(t *testing.T) {
	fe := flow.NewFlowExecutor(context.TODO(), "", api.NewConfiguration(), logrus.Fields{})
	pw := testSecret()
	totp := 1234567890
	formatted := fmt.Sprintf("%s%s%d", pw, flow.CodePasswordSeparator, totp)
	fe.SetSecrets(formatted, true)
	assert.Equal(t, formatted, fe.Answers[flow.StagePassword])
	assert.Equal(t, "", fe.Answers[flow.StageAuthenticatorValidate])
}

func TestFlowExecutor_SetSecrets_TOTP_NoCode(t *testing.T) {
	fe := flow.NewFlowExecutor(context.TODO(), "", api.NewConfiguration(), logrus.Fields{})
	pw := testSecret()
	fe.SetSecrets(pw, true)
	assert.Equal(t, pw, fe.Answers[flow.StagePassword])
	assert.Equal(t, "", fe.Answers[flow.StageAuthenticatorValidate])
	fe.SetSecrets(pw+flow.CodePasswordSeparator, true)
	assert.Equal(t, pw, fe.Answers[flow.StagePassword])
	assert.Equal(t, "", fe.Answers[flow.StageAuthenticatorValidate])
}
