package ldap

import (
	"errors"
	"net"
	"strings"

	"beryju.io/ldap"
	"github.com/getsentry/sentry-go"
	goldap "github.com/go-ldap/ldap/v3"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/outpost/ldap/search"
)

func (ls *LDAPServer) Search(bindDN string, searchReq ldap.SearchRequest, conn net.Conn) (ldap.ServerSearchResult, error) {
	req, span := search.NewRequest(bindDN, searchReq, conn)
	selectedApp := ""
	defer func() {
		span.Finish()
		metrics.Requests.With(prometheus.Labels{
			"outpost_name": ls.ac.Outpost.Name,
			"type":         "search",
			"app":          selectedApp,
		}).Observe(float64(span.EndTime.Sub(span.StartTime)))
		req.Log().WithField("took-ms", span.EndTime.Sub(span.StartTime).Milliseconds()).Info("Search request")
	}()

	defer func() {
		err := recover()
		if err == nil {
			return
		}
		log.WithError(err.(error)).Error("recover in search request")
		sentry.CaptureException(err.(error))
	}()

	parsedBaseDN, err := goldap.ParseDN(strings.ToLower(searchReq.BaseDN))
	if err != nil {
		req.Log().WithError(err).Info("failed to parse base DN")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("invalid DN")
	}
	parsedBindDN, err := goldap.ParseDN(strings.ToLower(bindDN))
	if err != nil {
		req.Log().WithError(err).Info("failed to parse bind DN")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("invalid DN")
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
				selectedApp = provider.GetAppSlug()
				longestMatch = len(provider.BaseDN)
			}
		}
	}
	if selectedProvider == nil {
		return ls.fallbackRootDSE(req)
	}
	// Route based on the base DN
	if len(searchReq.BaseDN) == 0 {
		return selectedProvider.searcher.SearchBase(req)
	}
	if strings.EqualFold(searchReq.BaseDN, "cn=subschema") {
		return selectedProvider.searcher.SearchSubschema(req)
	}
	return selectedProvider.searcher.Search(req)
}

func (ls *LDAPServer) fallbackRootDSE(req *search.Request) (ldap.ServerSearchResult, error) {
	req.Log().Trace("returning fallback Root DSE")
	return ldap.ServerSearchResult{
		Entries: []*ldap.Entry{
			{
				DN: "",
				Attributes: []*ldap.EntryAttribute{
					{
						Name:   "objectClass",
						Values: []string{"top", "OpenLDAProotDSE"},
					},
					{
						Name:   "subschemaSubentry",
						Values: []string{"cn=subschema"},
					},
					{
						Name:   "namingContexts",
						Values: []string{},
					},
				},
			},
		},
		Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess,
	}, nil

}
