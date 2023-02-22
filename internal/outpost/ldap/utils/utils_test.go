package utils

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
)

func Test_stringify_nil(t *testing.T) {
	var ex *string
	assert.Equal(t, ex, stringify(nil))
}

func TestAKAttrsToLDAP_String(t *testing.T) {
	u := api.User{}

	// normal string
	u.Attributes = map[string]interface{}{
		"foo": "bar",
	}
	assert.Equal(t, 1, len(AttributesToLDAP(u.Attributes, true)))
	assert.Equal(t, "foo", AttributesToLDAP(u.Attributes, true)[0].Name)
	assert.Equal(t, []string{"bar"}, AttributesToLDAP(u.Attributes, true)[0].Values)
	// pointer string
	u.Attributes = map[string]interface{}{
		"foo": api.PtrString("bar"),
	}
	assert.Equal(t, 1, len(AttributesToLDAP(u.Attributes, true)))
	assert.Equal(t, "foo", AttributesToLDAP(u.Attributes, true)[0].Name)
	assert.Equal(t, []string{"bar"}, AttributesToLDAP(u.Attributes, true)[0].Values)
}

func TestAKAttrsToLDAP_String_List(t *testing.T) {
	u := api.User{}
	// string list
	u.Attributes = map[string]interface{}{
		"foo": []string{"bar"},
	}
	assert.Equal(t, 1, len(AttributesToLDAP(u.Attributes, true)))
	assert.Equal(t, "foo", AttributesToLDAP(u.Attributes, true)[0].Name)
	assert.Equal(t, []string{"bar"}, AttributesToLDAP(u.Attributes, true)[0].Values)
	// pointer string list
	u.Attributes = map[string]interface{}{
		"foo": &[]string{"bar"},
	}
	assert.Equal(t, 1, len(AttributesToLDAP(u.Attributes, true)))
	assert.Equal(t, "foo", AttributesToLDAP(u.Attributes, true)[0].Name)
	assert.Equal(t, []string{"bar"}, AttributesToLDAP(u.Attributes, true)[0].Values)
}

func TestAKAttrsToLDAP_Dict(t *testing.T) {
	// dict
	d := map[string]interface{}{
		"foo": map[string]string{
			"foo": "bar",
		},
	}
	assert.Equal(t, 1, len(AttributesToLDAP(d, true)))
	assert.Equal(t, "foo", AttributesToLDAP(d, true)[0].Name)
	assert.Equal(t, []string{"map[foo:bar]"}, AttributesToLDAP(d, true)[0].Values)
}

func TestAKAttrsToLDAP_Mixed(t *testing.T) {
	// dict
	d := map[string]interface{}{
		"foo": []interface{}{
			"foo",
			6,
		},
	}
	assert.Equal(t, 1, len(AttributesToLDAP(d, true)))
	assert.Equal(t, "foo", AttributesToLDAP(d, true)[0].Name)
	assert.Equal(t, []string{"foo", "6"}, AttributesToLDAP(d, true)[0].Values)
}
