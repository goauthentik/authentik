package utils

import (
	"slices"
	"strings"
	"testing"

	"beryju.io/ldap"
	"github.com/stretchr/testify/assert"
	api "goauthentik.io/packages/client-go"
)

func Test_stringify_nil(t *testing.T) {
	var ex *string
	assert.Equal(t, ex, stringify(nil))
}

func TestAKAttrsToLDAP_String(t *testing.T) {
	u := api.User{}

	// normal string
	u.Attributes = map[string]any{
		"foo": "bar",
	}
	mapped := AttributesToLDAP(u.Attributes, func(key string) string {
		return AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	assert.Equal(t, 1, len(mapped))
	assert.Equal(t, "foo", mapped[0].Name)
	assert.Equal(t, []string{"bar"}, mapped[0].Values)
	// pointer string
	u.Attributes = map[string]any{
		"foo": new("bar"),
	}
	mapped = AttributesToLDAP(u.Attributes, func(key string) string {
		return AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	assert.Equal(t, 1, len(mapped))
	assert.Equal(t, "foo", mapped[0].Name)
	assert.Equal(t, []string{"bar"}, mapped[0].Values)
}

func TestAKAttrsToLDAP_String_List(t *testing.T) {
	u := api.User{}
	// string list
	u.Attributes = map[string]any{
		"foo": []string{"bar"},
	}
	mapped := AttributesToLDAP(u.Attributes, func(key string) string {
		return AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	assert.Equal(t, 1, len(mapped))
	assert.Equal(t, "foo", mapped[0].Name)
	assert.Equal(t, []string{"bar"}, mapped[0].Values)
	// pointer string list
	u.Attributes = map[string]any{
		"foo": &[]string{"bar"},
	}
	mapped = AttributesToLDAP(u.Attributes, func(key string) string {
		return AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	assert.Equal(t, 1, len(mapped))
	assert.Equal(t, "foo", mapped[0].Name)
	assert.Equal(t, []string{"bar"}, mapped[0].Values)
}

func TestAKAttrsToLDAP_Dict(t *testing.T) {
	// dict
	d := map[string]any{
		"foo": map[string]string{
			"foo": "bar",
		},
	}
	mapped := AttributesToLDAP(d, func(key string) string {
		return AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	assert.Equal(t, 1, len(mapped))
	assert.Equal(t, "foo", mapped[0].Name)
	assert.Equal(t, []string{"map[foo:bar]"}, mapped[0].Values)
}

func TestAKAttrsToLDAP_Mixed(t *testing.T) {
	// dict
	d := map[string]any{
		"foo": []any{
			"foo",
			6,
		},
	}
	mapped := AttributesToLDAP(d, func(key string) string {
		return AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	assert.Equal(t, 1, len(mapped))
	assert.Equal(t, "foo", mapped[0].Name)
	assert.Equal(t, []string{"foo", "6"}, mapped[0].Values)
}

func TestAKNestedAttrsToLDAP_onelevel(t *testing.T) {
	d := map[string]any{
		"bar": map[string]any{
			"baz": "quux",
		},
	}
	mapped := AttributesToLDAP(d, func(key string) string {
		return AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	assert.Equal(t, 1, len(mapped))
	assert.Equal(t, "bar--baz", mapped[0].Name)
	assert.Equal(t, []string{"quux"}, mapped[0].Values)
}

func TestAKNestedAttrsToLDAP_multiple_levels(t *testing.T) {
	d := map[string]any{
		"foo": map[string]any{
			"bar": map[string]any{
				"baz": "quux",
			},
		},
	}
	mapped := AttributesToLDAP(d, func(key string) string {
		return AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	assert.Equal(t, 1, len(mapped))
	assert.Equal(t, "foo--bar--baz", mapped[0].Name)
	assert.Equal(t, []string{"quux"}, mapped[0].Values)
}

func TestAKNestedAttrsToLDAP_more_than_one_attr(t *testing.T) {
	d := map[string]any{
		"root": "value",
		"lorem": map[string]any{
			"ipsum": "dolor",
		},
		"foo": map[string]any{
			"bar": map[string]any{
				"baz": "quux",
			},
		},
	}
	mapped := AttributesToLDAP(d, func(key string) string {
		return AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	assert.Equal(t, 3, len(mapped))

	slices.SortFunc(mapped, func(a, b *ldap.EntryAttribute) int {
		return strings.Compare(strings.ToLower(a.Name), strings.ToLower(b.Name))
	})

	assert.Equal(t, "foo--bar--baz", mapped[0].Name)
	assert.Equal(t, []string{"quux"}, mapped[0].Values)
	assert.Equal(t, "lorem--ipsum", mapped[1].Name)
	assert.Equal(t, []string{"dolor"}, mapped[1].Values)
	assert.Equal(t, "root", mapped[2].Name)
	assert.Equal(t, []string{"value"}, mapped[2].Values)
}
