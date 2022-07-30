package utils

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
)

func Test_ldapResolveTypeSingle_nil(t *testing.T) {
	var ex *string
	assert.Equal(t, ex, ldapResolveTypeSingle(nil))
}

func TestAKAttrsToLDAP_String(t *testing.T) {
	u := api.User{}

	// normal string
	u.Attributes = map[string]interface{}{
		"foo": "bar",
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(u.Attributes)))
	assert.Equal(t, "foo", AKAttrsToLDAP(u.Attributes)[0].Name)
	assert.Equal(t, []string{"bar"}, AKAttrsToLDAP(u.Attributes)[0].Values)
	// pointer string
	u.Attributes = map[string]interface{}{
		"foo": api.PtrString("bar"),
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(u.Attributes)))
	assert.Equal(t, "foo", AKAttrsToLDAP(u.Attributes)[0].Name)
	assert.Equal(t, []string{"bar"}, AKAttrsToLDAP(u.Attributes)[0].Values)
}

func TestAKAttrsToLDAP_String_List(t *testing.T) {
	u := api.User{}
	// string list
	u.Attributes = map[string]interface{}{
		"foo": []string{"bar"},
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(u.Attributes)))
	assert.Equal(t, "foo", AKAttrsToLDAP(u.Attributes)[0].Name)
	assert.Equal(t, []string{"bar"}, AKAttrsToLDAP(u.Attributes)[0].Values)
	// pointer string list
	u.Attributes = map[string]interface{}{
		"foo": &[]string{"bar"},
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(u.Attributes)))
	assert.Equal(t, "foo", AKAttrsToLDAP(u.Attributes)[0].Name)
	assert.Equal(t, []string{"bar"}, AKAttrsToLDAP(u.Attributes)[0].Values)
}

func TestAKAttrsToLDAP_Dict(t *testing.T) {
	// dict
	d := map[string]interface{}{
		"foo": map[string]string{
			"foo": "bar",
		},
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(d)))
	assert.Equal(t, "foo", AKAttrsToLDAP(d)[0].Name)
	// Dicts are currently unsupported, but make sure we don't crash
	assert.Equal(t, []string([]string(nil)), AKAttrsToLDAP(d)[0].Values)
}

func TestAKAttrsToLDAP_Mixed(t *testing.T) {
	// dict
	d := map[string]interface{}{
		"foo": []interface{}{
			"foo",
			6,
		},
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(d)))
	assert.Equal(t, "foo", AKAttrsToLDAP(d)[0].Name)
	// Dicts are currently unsupported, but make sure we don't crash
	assert.Equal(t, []string{"foo", ""}, AKAttrsToLDAP(d)[0].Values)
}
