package flow

import (
	"testing"

	"github.com/stretchr/testify/assert"
	api "goauthentik.io/packages/client-go"
)

func TestConvert(t *testing.T) {
	var a challengeCommon = api.NewIdentificationChallengeWithDefaults()
	assert.NotNil(t, a)
}
