package utils

import (
	"beryju.io/ldap"
	goldap "github.com/go-ldap/ldap/v3"
	ber "github.com/nmcclain/asn1-ber"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/constants"
)

func ParseFilterForUser(req api.ApiCoreUsersListRequest, f *ber.Packet, skip bool) (api.ApiCoreUsersListRequest, bool) {
	switch f.Tag {
	case ldap.FilterEqualityMatch:
		return parseFilterForUserSingle(req, f)
	case ldap.FilterAnd:
		for _, child := range f.Children {
			r, s := ParseFilterForUser(req, child, skip)
			skip = skip || s
			req = r
		}
		return req, skip
	}
	return req, skip
}

func parseFilterForUserSingle(req api.ApiCoreUsersListRequest, f *ber.Packet) (api.ApiCoreUsersListRequest, bool) {
	// We can only handle key = value pairs here
	if len(f.Children) < 2 {
		return req, false
	}
	k := f.Children[0].Value
	// Ensure key is string
	if _, ok := k.(string); !ok {
		return req, false
	}
	v := f.Children[1].Value
	// Null values are ignored
	if v == nil {
		return req, false
	}
	val := stringify(v)
	if val == nil {
		return req, false
	}
	switch k {
	case "cn":
		return req.Username(*val), false
	case "name":
	case "displayName":
		return req.Name(*val), false
	case "mail":
		return req.Email(*val), false
	case "member":
		fallthrough
	case "memberOf":
		groupDN, err := goldap.ParseDN(*val)
		if err != nil {
			return req.GroupsByName([]string{*val}), false
		}
		name := groupDN.RDNs[0].Attributes[0].Value
		// If the DN's first ou is virtual-groups, ignore this filter
		if len(groupDN.RDNs) > 1 {
			if groupDN.RDNs[1].Attributes[0].Value == constants.OUUsers || groupDN.RDNs[1].Attributes[0].Value == constants.OUVirtualGroups {
				// Since we know we're not filtering anything, skip this request
				return req, true
			}
		}
		return req.GroupsByName([]string{name}), false
	}
	return req, false
}
