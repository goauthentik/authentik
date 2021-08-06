package ldap

import (
	"context"
	"errors"
	"net"
	"strings"

	"github.com/getsentry/sentry-go"
	goldap "github.com/go-ldap/ldap/v3"
	"github.com/google/uuid"
	"github.com/nmcclain/ldap"
	log "github.com/sirupsen/logrus"
)

type SearchRequest struct {
	ldap.SearchRequest
	BindDN string
	id     string
	conn   net.Conn
	log    *log.Entry
	ctx    context.Context
}

func (ls *LDAPServer) Search(bindDN string, searchReq ldap.SearchRequest, conn net.Conn) (ldap.ServerSearchResult, error) {
	span := sentry.StartSpan(context.TODO(), "authentik.providers.ldap.search", sentry.TransactionName("authentik.providers.ldap.search"))
	span.SetTag("user.username", bindDN)
	span.SetTag("ak_filter", searchReq.Filter)
	span.SetTag("ak_base_dn", searchReq.BaseDN)

	bindDN = strings.ToLower(bindDN)
	rid := uuid.New().String()
	req := SearchRequest{
		SearchRequest: searchReq,
		BindDN:        bindDN,
		conn:          conn,
		log:           ls.log.WithField("bindDN", bindDN).WithField("requestId", rid).WithField("client", conn.RemoteAddr().String()).WithField("filter", searchReq.Filter).WithField("baseDN", searchReq.BaseDN),
		id:            rid,
		ctx:           span.Context(),
	}

	defer func() {
		span.Finish()
		req.log.WithField("took-ms", span.EndTime.Sub(span.StartTime).Milliseconds()).Info("Search request")
	}()

	defer func() {
		err := recover()
		if err == nil {
			return
		}
		log.WithError(err.(error)).Error("recover in serach request")
		sentry.CaptureException(err.(error))
	}()

	if searchReq.BaseDN == "" {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultSuccess}, nil
	}
	bd, err := goldap.ParseDN(searchReq.BaseDN)
	if err != nil {
		req.log.WithError(err).Info("failed to parse basedn")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("invalid DN")
	}
	for _, provider := range ls.providers {
		providerBase, _ := goldap.ParseDN(provider.BaseDN)
		if providerBase.AncestorOf(bd) {
			return provider.Search(req)
		}
	}
	return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("no provider could handle request")
}
