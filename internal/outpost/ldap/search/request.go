package search

import (
	"context"
	"fmt"
	"net"
	"strings"

	"beryju.io/ldap"
	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/utils"
)

type Request struct {
	ldap.SearchRequest
	BindDN string
	log    *log.Entry

	id   string
	conn net.Conn
	ctx  context.Context
}

func NewRequest(bindDN string, searchReq ldap.SearchRequest, conn net.Conn) (*Request, *sentry.Span) {
	rid := uuid.New().String()
	bindDN = strings.ToLower(bindDN)
	span := sentry.StartSpan(context.TODO(), "authentik.providers.ldap.search", sentry.WithTransactionName("authentik.providers.ldap.search"))
	span.Description = fmt.Sprintf("%s (%s)", searchReq.BaseDN, ldap.ScopeMap[searchReq.Scope])
	span.SetTag("request_uid", rid)
	hub := sentry.GetHubFromContext(span.Context())
	if hub == nil {
		hub = sentry.CurrentHub()
	}
	hub.Scope().SetUser(sentry.User{
		Username:  bindDN,
		ID:        bindDN,
		IPAddress: utils.GetIP(conn.RemoteAddr()),
	})
	span.SetTag("ldap_filter", searchReq.Filter)
	span.SetTag("ldap_base_dn", searchReq.BaseDN)
	return &Request{
		SearchRequest: searchReq,
		BindDN:        bindDN,
		conn:          conn,
		log:           log.WithField("bindDN", bindDN).WithField("requestId", rid).WithField("scope", ldap.ScopeMap[searchReq.Scope]).WithField("client", utils.GetIP(conn.RemoteAddr())).WithField("filter", searchReq.Filter).WithField("baseDN", searchReq.BaseDN),
		id:            rid,
		ctx:           span.Context(),
	}, span
}

func (r *Request) Context() context.Context {
	return r.ctx
}

func (r *Request) Log() *log.Entry {
	return r.log
}

func (r *Request) RemoteAddr() string {
	return utils.GetIP(r.conn.RemoteAddr())
}
