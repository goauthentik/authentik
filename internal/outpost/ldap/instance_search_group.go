package ldap

import (
	ber "github.com/nmcclain/asn1-ber"
	"github.com/nmcclain/ldap"
	"goauthentik.io/api"
)

func parseFilterForGroup(req api.ApiCoreGroupsListRequest, filter string) api.ApiCoreGroupsListRequest {
	f, err := ldap.CompileFilter(filter)
	if err != nil {
		return req
	}
	switch f.Tag {
	case ldap.FilterEqualityMatch:
		return parseFilterForGroupSingle(req, f)
	case ldap.FilterAnd:
		for _, child := range f.Children {
			req = parseFilterForGroupSingle(req, child)
		}
		return req
	}
	return req
}

func parseFilterForGroupSingle(req api.ApiCoreGroupsListRequest, f *ber.Packet) api.ApiCoreGroupsListRequest {
	v := f.Children[1].Value.(string)
	switch f.Children[0].Value.(string) {
	case "cn":
		return req.Name(v)
	}
	return req
}
