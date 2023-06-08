package ldap

import (
	"strings"

	"beryju.io/ldap"
	goldap "github.com/go-ldap/ldap/v3"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/search"
)

func (ls *LDAPServer) providerForRequest(req *search.Request) *ProviderInstance {
	parsedBaseDN, err := goldap.ParseDN(strings.ToLower(req.BaseDN))
	if err != nil {
		req.Log().WithError(err).Info("failed to parse base DN")
		return nil
	}
	parsedBindDN, err := goldap.ParseDN(strings.ToLower(req.BindDN))
	if err != nil {
		req.Log().WithError(err).Info("failed to parse bind DN")
		return nil
	}
	var selectedProvider *ProviderInstance
	longestMatch := 0
	for _, provider := range ls.providers {
		providerBase, _ := goldap.ParseDN(strings.ToLower(provider.BaseDN))
		// Try to match the provider primarily based on the search request's base DN
		baseDNMatches := providerBase.AncestorOf(parsedBaseDN) || providerBase.Equal(parsedBaseDN)
		// But also try to match the provider based on the bind DN
		bindDNMatches := providerBase.AncestorOf(parsedBindDN) || providerBase.Equal(parsedBindDN)
		if baseDNMatches || bindDNMatches {
			// Only select the provider if it's a more precise match than previously
			if len(provider.BaseDN) > longestMatch {
				req.Log().WithField("provider", provider.BaseDN).Trace("selecting provider for search request")
				selectedProvider = provider
				longestMatch = len(provider.BaseDN)
			}
		}
	}
	return selectedProvider
}

func (ls *LDAPServer) searchRoute(req *search.Request, pi *ProviderInstance) (ldap.ServerSearchResult, error) {
	// Route based on the base DN
	if len(req.BaseDN) == 0 {
		req.Log().Trace("routing to base")
		return pi.searcher.SearchBase(req)
	}
	if strings.EqualFold(req.BaseDN, "cn=subschema") || req.FilterObjectClass == constants.OCSubSchema {
		req.Log().Trace("routing to subschema")
		return pi.searcher.SearchSubschema(req)
	}
	req.Log().Trace("routing to default")
	return pi.searcher.Search(req)
}

func (ls *LDAPServer) filterResultAttributes(req *search.Request, result ldap.ServerSearchResult) ldap.ServerSearchResult {
	allowedAttributes := []string{}
	if len(req.Attributes) == 1 && req.Attributes[0] == constants.SearchAttributeNone {
		allowedAttributes = []string{"objectClass"}
	}
	if len(req.Attributes) > 0 {
		// Only strictly filter allowed attributes if we haven't already narrowed the attributes
		// down
		if len(allowedAttributes) < 1 {
			allowedAttributes = req.Attributes
		}
		// Filter LDAP returned attributes by search requested attributes, taking "1.1"
		// into consideration
		return req.FilterLDAPAttributes(result, func(attr *ldap.EntryAttribute) bool {
			for _, allowed := range allowedAttributes {
				if allowed == constants.SearchAttributeAllUser ||
					allowed == constants.SearchAttributeAllOperational {
					return true
				}
				if strings.EqualFold(allowed, attr.Name) {
					return true
				}
			}
			return false
		})
	}
	return result
}
