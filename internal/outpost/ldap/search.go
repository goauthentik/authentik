package ldap

import (
	"errors"
	"net"
	"strings"

	"github.com/getsentry/sentry-go"
	goldap "github.com/go-ldap/ldap/v3"
	"github.com/nmcclain/ldap"
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

	if searchReq.BaseDN == "" {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultSuccess}, nil
	}
	bd, err := goldap.ParseDN(strings.ToLower(searchReq.BaseDN))
	if err != nil {
		req.Log().WithError(err).Info("failed to parse basedn")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("invalid DN")
	}
	for _, provider := range ls.providers {
		providerBase, _ := goldap.ParseDN(strings.ToLower(provider.BaseDN))
		if providerBase.AncestorOf(bd) || providerBase.Equal(bd) {
			selectedApp = provider.GetAppSlug()
			return provider.searcher.Search(req)
		}
	}
	return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("no provider could handle request")
}
