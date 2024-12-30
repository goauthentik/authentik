package search

import (
	"context"
	"fmt"
	"net"
	"strings"

	"beryju.io/ldap"
	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	"go.uber.org/zap"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils"
)

type Request struct {
	ldap.SearchRequest
	BindDN            string
	FilterObjectClass string
	log               *zap.Logger

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
	l := config.Get().Logger().With(
		zap.String("bindDN", bindDN),
		zap.String("baseDN", searchReq.BaseDN),
		zap.String("requestId", rid),
		zap.String("scope", ldap.ScopeMap[searchReq.Scope]),
		zap.String("client", utils.GetIP(conn.RemoteAddr())),
		zap.String("filter", searchReq.Filter),
	)
	filterOC, err := ldap.GetFilterObjectClass(searchReq.Filter)
	if err != nil && len(searchReq.Filter) > 0 {
		l.Warn("invalid filter object class", zap.Error(err), zap.String("objectClass", filterOC))
	}
	return &Request{
		SearchRequest:     searchReq,
		BindDN:            bindDN,
		FilterObjectClass: filterOC,
		conn:              conn,
		log:               l,
		id:                rid,
		ctx:               span.Context(),
	}, span
}

func (r *Request) Context() context.Context {
	return r.ctx
}

func (r *Request) Log() *zap.Logger {
	return r.log
}

func (r *Request) RemoteAddr() string {
	return utils.GetIP(r.conn.RemoteAddr())
}
