package utils

import (
	"strings"

	"beryju.io/ldap"
	goldap "github.com/go-ldap/ldap/v3"
	ber "github.com/nmcclain/asn1-ber"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/constants"
)

func ParseFilterForGroup(req api.ApiCoreGroupsListRequest, f *ber.Packet, skip bool) (api.ApiCoreGroupsListRequest, bool) {
	switch f.Tag {
	case ldap.FilterEqualityMatch:
		return parseFilterForGroupSingle(req, f)
	case ldap.FilterAnd:
		for _, child := range f.Children {
			r, s := ParseFilterForGroup(req, child, skip)
			skip = skip || s
			req = r
		}
		return req, skip
	}
	return req, skip
}

func parseFilterForGroupSingle(req api.ApiCoreGroupsListRequest, f *ber.Packet) (api.ApiCoreGroupsListRequest, bool) {
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
	// Check key
	switch strings.ToLower(k.(string)) {
	case "cn":
		return req.Name(*val), false
	case "member":
		fallthrough
	case "memberOf":
		userDN, err := goldap.ParseDN(*val)
		if err != nil {
			return req.MembersByUsername([]string{*val}), false
		}
		username := userDN.RDNs[0].Attributes[0].Value
		// If the DN's first ou is virtual-groups, ignore this filter
		if len(userDN.RDNs) > 1 {
			if strings.EqualFold(userDN.RDNs[1].Attributes[0].Value, constants.OUVirtualGroups) || strings.EqualFold(userDN.RDNs[1].Attributes[0].Value, constants.OUGroups) {
				// Since we know we're not filtering anything, skip this request
				return req, true
			}
		}
		return req.MembersByUsername([]string{username}), false
	}
	return req, false
}
