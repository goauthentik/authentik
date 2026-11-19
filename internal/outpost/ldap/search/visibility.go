package search

import (
	"context"

	api "goauthentik.io/packages/client-go"
)

// Visibility is the set of users and groups a provider exposes when it limits
// search to users with access to its application. A nil *Visibility means no
// limit: every method returns its input unchanged.
type Visibility struct {
	users  map[int32]struct{}
	groups map[string]struct{}
}

// FetchVisibility returns the provider's visible users and groups, or nil if
// the provider doesn't limit search.
func FetchVisibility(ctx context.Context, client *api.APIClient, providerPk int32, enabled bool) (*Visibility, error) {
	if !enabled {
		return nil, nil
	}
	res, _, err := client.OutpostsAPI.OutpostsLdapSearchVisibility(ctx, providerPk).Execute()
	if err != nil {
		return nil, err
	}
	return NewVisibility(res.Users, res.Groups), nil
}

func NewVisibility(users []int32, groups []string) *Visibility {
	v := &Visibility{
		users:  make(map[int32]struct{}, len(users)),
		groups: make(map[string]struct{}, len(groups)),
	}
	for _, pk := range users {
		v.users[pk] = struct{}{}
	}
	for _, pk := range groups {
		v.groups[pk] = struct{}{}
	}
	return v
}

func (v *Visibility) hasUser(pk int32) bool {
	_, ok := v.users[pk]
	return ok
}

func (v *Visibility) hasGroup(pk string) bool {
	_, ok := v.groups[pk]
	return ok
}

// FilterUsers drops hidden users, and hidden groups from the remaining users' memberships.
func (v *Visibility) FilterUsers(users []api.User) []api.User {
	if v == nil {
		return users
	}
	out := make([]api.User, 0, len(users))
	for _, u := range users {
		if !v.hasUser(u.Pk) {
			continue
		}
		u.Groups = filter(u.Groups, v.hasGroup)
		u.GroupsObj = filter(u.GroupsObj, func(g api.PartialGroup) bool { return v.hasGroup(g.Pk) })
		out = append(out, u)
	}
	return out
}

// FilterGroups drops hidden groups, and hidden users and groups from the
// remaining groups' members, parents and children, so no entry references an
// object that isn't visible.
func (v *Visibility) FilterGroups(groups []api.Group) []api.Group {
	if v == nil {
		return groups
	}
	related := func(g api.RelatedGroup) bool { return v.hasGroup(g.Pk) }
	out := make([]api.Group, 0, len(groups))
	for _, g := range groups {
		if !v.hasGroup(g.Pk) {
			continue
		}
		g.Users = filter(g.Users, v.hasUser)
		g.UsersObj = filter(g.UsersObj, func(u api.PartialUser) bool { return v.hasUser(u.Pk) })
		g.Parents = filter(g.Parents, v.hasGroup)
		g.ParentsObj = filter(g.ParentsObj, related)
		g.Children = filter(g.Children, v.hasGroup)
		g.ChildrenObj = filter(g.ChildrenObj, related)
		out = append(out, g)
	}
	return out
}

// filter returns a new slice, so the caller's (possibly shared) backing array is never modified.
func filter[T any](items []T, keep func(T) bool) []T {
	if items == nil {
		return nil
	}
	out := make([]T, 0, len(items))
	for _, item := range items {
		if keep(item) {
			out = append(out, item)
		}
	}
	return out
}
