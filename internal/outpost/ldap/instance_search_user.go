package ldap

import (
	ber "github.com/nmcclain/asn1-ber"
	"github.com/nmcclain/ldap"
	"goauthentik.io/api"
)

func parseFilterForUser(req api.ApiCoreUsersListRequest, filter string) api.ApiCoreUsersListRequest {
	f, err := ldap.CompileFilter(filter)
	if err != nil {
		return req
	}
	switch f.Tag {
	case ldap.FilterEqualityMatch:
		return parseFilterForUserSingle(req, f)
	case ldap.FilterAnd:
		for _, child := range f.Children {
			req = parseFilterForUserSingle(req, child)
		}
		return req
	}
	return req
}

func parseFilterForUserSingle(req api.ApiCoreUsersListRequest, f *ber.Packet) api.ApiCoreUsersListRequest {
	v := f.Children[1].Value.(string)
	switch f.Children[0].Value.(string) {
	case "cn":
		return req.Username(v)
	case "name":
	case "displayName":
		return req.Name(v)
	case "mail":
		return req.Email(v)
	}
	return req
}
