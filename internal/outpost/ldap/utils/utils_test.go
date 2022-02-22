package utils

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api"
)

func TestAKAttrsToLDAP_String(t *testing.T) {
	var d *map[string]interface{}

	// normal string
	d = &map[string]interface{}{
		"foo": "bar",
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(d)))
	assert.Equal(t, "foo", AKAttrsToLDAP(d)[0].Name)
	assert.Equal(t, []string{"bar"}, AKAttrsToLDAP(d)[0].Values)
	// pointer string
	d = &map[string]interface{}{
		"foo": api.PtrString("bar"),
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(d)))
	assert.Equal(t, "foo", AKAttrsToLDAP(d)[0].Name)
	assert.Equal(t, []string{"bar"}, AKAttrsToLDAP(d)[0].Values)
}

func TestAKAttrsToLDAP_String_List(t *testing.T) {
	var d *map[string]interface{}
	// string list
	d = &map[string]interface{}{
		"foo": []string{"bar"},
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(d)))
	assert.Equal(t, "foo", AKAttrsToLDAP(d)[0].Name)
	assert.Equal(t, []string{"bar"}, AKAttrsToLDAP(d)[0].Values)
	// pointer string list
	d = &map[string]interface{}{
		"foo": &[]string{"bar"},
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(d)))
	assert.Equal(t, "foo", AKAttrsToLDAP(d)[0].Name)
	assert.Equal(t, []string{"bar"}, AKAttrsToLDAP(d)[0].Values)
}

func TestAKAttrsToLDAP_Dict(t *testing.T) {
	// dict
	d := &map[string]interface{}{
		"foo": map[string]string{
			"foo": "bar",
		},
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(d)))
	assert.Equal(t, "foo", AKAttrsToLDAP(d)[0].Name)
	// Dicts are currently unsupported, but make sure we don't crash
	// assert.Equal(t, []string{nil}, AKAttrsToLDAP(d)[0].Values)
}

func TestAKAttrsToLDAP_Mixed(t *testing.T) {
	// dict
	d := &map[string]interface{}{
		"foo": []interface{}{
			"foo",
			6,
		},
	}
	assert.Equal(t, 1, len(AKAttrsToLDAP(d)))
	assert.Equal(t, "foo", AKAttrsToLDAP(d)[0].Name)
	// Dicts are currently unsupported, but make sure we don't crash
	// assert.Equal(t, []string{nil}, AKAttrsToLDAP(d)[0].Values)
}
