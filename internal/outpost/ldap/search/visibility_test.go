package search

import (
	"testing"

	"github.com/stretchr/testify/assert"
	api "goauthentik.io/packages/client-go"
)

const (
	visibleGroup = "00000000-0000-0000-0000-00000000000a"
	hiddenGroup  = "00000000-0000-0000-0000-00000000000b"
)

func TestVisibilityNilKeepsEverything(t *testing.T) {
	var v *Visibility
	users := []api.User{{Pk: 1}, {Pk: 2}}
	groups := []api.Group{{Pk: visibleGroup}, {Pk: hiddenGroup}}
	assert.Equal(t, users, v.FilterUsers(users))
	assert.Equal(t, groups, v.FilterGroups(groups))
}

func TestVisibilityFilterUsers(t *testing.T) {
	v := NewVisibility([]int32{1}, []string{visibleGroup})
	users := []api.User{
		{
			Pk:     1,
			Groups: []string{visibleGroup, hiddenGroup},
			GroupsObj: []api.PartialGroup{
				{Pk: visibleGroup},
				{Pk: hiddenGroup},
			},
		},
		{Pk: 2},
	}
	out := v.FilterUsers(users)
	assert.Len(t, out, 1)
	assert.Equal(t, int32(1), out[0].Pk)
	assert.Equal(t, []string{visibleGroup}, out[0].Groups)
	assert.Equal(t, []api.PartialGroup{{Pk: visibleGroup}}, out[0].GroupsObj)
	// The input must not be modified, it may be shared with other searches.
	assert.Len(t, users[0].Groups, 2)
}

func TestVisibilityFilterGroups(t *testing.T) {
	v := NewVisibility([]int32{1}, []string{visibleGroup})
	groups := []api.Group{
		{
			Pk:          visibleGroup,
			Users:       []int32{1, 2},
			UsersObj:    []api.PartialUser{{Pk: 1}, {Pk: 2}},
			Parents:     []string{hiddenGroup},
			ParentsObj:  []api.RelatedGroup{{Pk: hiddenGroup}},
			Children:    []string{hiddenGroup},
			ChildrenObj: []api.RelatedGroup{{Pk: hiddenGroup}},
		},
		{Pk: hiddenGroup},
	}
	out := v.FilterGroups(groups)
	assert.Len(t, out, 1)
	g := out[0]
	assert.Equal(t, visibleGroup, g.Pk)
	assert.Equal(t, []int32{1}, g.Users)
	assert.Equal(t, []api.PartialUser{{Pk: 1}}, g.UsersObj)
	assert.Empty(t, g.Parents)
	assert.Empty(t, g.ParentsObj)
	assert.Empty(t, g.Children)
	assert.Empty(t, g.ChildrenObj)
	// The input must not be modified, it may be shared with other searches.
	assert.Len(t, groups[0].Users, 2)
}

func TestVisibilityEmptyHidesEverything(t *testing.T) {
	v := NewVisibility(nil, nil)
	assert.Empty(t, v.FilterUsers([]api.User{{Pk: 1}}))
	assert.Empty(t, v.FilterGroups([]api.Group{{Pk: visibleGroup}}))
}
