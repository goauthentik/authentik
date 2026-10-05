package ldap

import (
	"net"
	"time"
	"fmt"

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
		}).Observe(float64(span.EndTime.Sub(span.StartTime)) / float64(time.Second))
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

// fully escapes the bytes in string using the "\00" style escape sequence
// as documented https://learn.microsoft.com/en-us/windows/win32/ad/creating-a-query-filter
func escapeString(s string) string {
	b := []byte(s)
	r := ""
	for i := range b {
		r += fmt.Sprintf("\\%02x", b[i])
	}
	return r
}

func (ls *LDAPServer) Compare(boundDN string, req ldap.CompareRequest, conn net.Conn) (ldap.LDAPResultCode, error) {
	// search for entry referred to by req.DN
	searchReq := ldap.NewSearchRequest(req.DN, ldap.ScopeBaseObject, ldap.DerefAlways, 0, 0, true, "(objectClass=*)", []string{}, []ldap.Control{})
	searchResult, err := ls.Search(boundDN, *searchReq, conn)
	if err != nil {
		return searchResult.ResultCode, err
	}
	if len(searchResult.Entries) != 1 {
		return ldap.LDAPResultNoSuchObject, nil
	}

	// transform assertions into a filter string
	// TODO: Create the ber.Packet directly, instead of relying so heavily on ldap.CompileFilter?
	searchFilter := "(&"
	for _, ava := range req.AVA {
		searchFilter += "("
		searchFilter += escapeString(ava.AttributeDesc)
		searchFilter += "="
		searchFilter += escapeString(ava.AssertionValue)
		searchFilter += ")"
	}
	searchFilter += ")"

	// compile & apply filter
	compiledFilter, err := ldap.CompileFilter(searchFilter)
	if err != nil {
		return ldap.LDAPResultOperationsError, err
	}
	equal, resultCode := ldap.ServerApplyFilter(compiledFilter, searchResult.Entries[0])
	if resultCode != ldap.LDAPResultSuccess {
		return resultCode, nil
	}

	if equal {
		return ldap.LDAPResultCompareTrue, nil
	}

	return ldap.LDAPResultCompareFalse, nil
}
