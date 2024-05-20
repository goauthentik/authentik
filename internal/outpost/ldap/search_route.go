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
