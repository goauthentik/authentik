package ldap

import (
	"net"

	"beryju.io/ldap"
	"github.com/getsentry/sentry-go"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ldap/constants"
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
		req.Log().WithField("attributes", searchReq.Attributes).WithField("took-ms", span.EndTime.Sub(span.StartTime).Milliseconds()).Info("Search request")
	}()

	defer func() {
		err := recover()
		if err == nil {
			return
		}
		log.WithError(err.(error)).Error("recover in search request")
		sentry.CaptureException(err.(error))
	}()

	selectedProvider := ls.providerForRequest(req)
	if selectedProvider == nil {
		return ls.fallbackRootDSE(req)
	}
	selectedApp = selectedProvider.GetAppSlug()
	result, err := ls.searchRoute(req, selectedProvider)
	return result, err
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
						Values: []string{constants.OCTop},
					},
					{
						Name:   "entryDN",
						Values: []string{""},
					},
					{
						Name:   "subschemaSubentry",
						Values: []string{"cn=subschema"},
					},
					{
						Name:   "namingContexts",
						Values: []string{},
					},
					{
						Name: "description",
						Values: []string{
							"This LDAP server requires an authenticated session.",
						},
					},
				},
			},
		},
		Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess,
	}, nil

}
