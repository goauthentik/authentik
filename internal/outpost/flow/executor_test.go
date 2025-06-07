package flow

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
)

func TestConvert(t *testing.T) {
	var a challengeCommon = api.NewIdentificationChallengeWithDefaults()
	assert.NotNil(t, a)
}
