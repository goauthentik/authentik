package ldap

import (
	"errors"
	"net"

	"github.com/getsentry/sentry-go"
	goldap "github.com/go-ldap/ldap/v3"
	"github.com/nmcclain/ldap"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/outpost/ldap/search"
	"goauthentik.io/internal/utils"
)

func (ls *LDAPServer) Search(bindDN string, searchReq ldap.SearchRequest, conn net.Conn) (ldap.ServerSearchResult, error) {
	req, span := search.NewRequest(bindDN, searchReq, conn)

	defer func() {
		span.Finish()
		metrics.Requests.With(prometheus.Labels{
			"outpost_name": ls.ac.Outpost.Name,
			"type":         "search",
			"filter":       req.Filter,
			"dn":           req.BindDN,
			"client":       utils.GetIP(conn.RemoteAddr()),
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
	bd, err := goldap.ParseDN(searchReq.BaseDN)
	if err != nil {
		req.Log().WithError(err).Info("failed to parse basedn")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("invalid DN")
	}
	for _, provider := range ls.providers {
		providerBase, _ := goldap.ParseDN(provider.BaseDN)
		if providerBase.AncestorOf(bd) || providerBase.Equal(bd) {
			return provider.searcher.Search(req)
		}
	}
	return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("no provider could handle request")
}
