package ldap

import (
	goldap "github.com/go-ldap/ldap/v3"
	ber "github.com/nmcclain/asn1-ber"
	"github.com/nmcclain/ldap"
	"goauthentik.io/api"
)

func parseFilterForGroup(req api.ApiCoreGroupsListRequest, f *ber.Packet) api.ApiCoreGroupsListRequest {
	switch f.Tag {
	case ldap.FilterEqualityMatch:
		return parseFilterForGroupSingle(req, f)
	case ldap.FilterAnd:
		for _, child := range f.Children {
			req = parseFilterForGroup(req, child)
		}
		return req
	}
	return req
}

func parseFilterForGroupSingle(req api.ApiCoreGroupsListRequest, f *ber.Packet) api.ApiCoreGroupsListRequest {
	// We can only handle key = value pairs here
	if len(f.Children) < 2 {
		return req
	}
	k := f.Children[0].Value
	// Ensure key is string
	if _, ok := k.(string); !ok {
		return req
	}
	v := f.Children[1].Value
	// Null values are ignored
	if v == nil {
		return req
	}
	// Switch on type of the value, then check the key
	switch vv := v.(type) {
	case string:
		switch k {
		case "cn":
			return req.Name(vv)
		case "member":
		case "memberOf":
			userDN, err := goldap.ParseDN(vv)
			if err != nil {
				return req
			}
			username := userDN.RDNs[0].Attributes[0].Value
			return req.MembersByUsername([]string{username})
		}
	// TODO: Support int
	default:
		return req
	}
	return req
}
