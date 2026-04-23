package bind

import (
	"context"
	"net"
	"strings"

	"beryju.io/ldap"
	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/utils"
)

type Request struct {
	ldap.BindRequest
	id   string
	conn net.Conn
	log  *log.Entry
	ctx  context.Context
}

func NewRequest(req ldap.BindRequest, conn net.Conn) (*Request, *sentry.Span) {
	bindDN := strings.ToLower(req.BindDN)
	req.BindDN = bindDN

	span := sentry.StartSpan(context.TODO(), "authentik.providers.ldap.bind",
		sentry.WithTransactionName("authentik.providers.ldap.bind"))
	span.Description = bindDN
	rid := uuid.New().String()
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

	bindDN = strings.ToLower(bindDN)
	return &Request{
		BindRequest: req,
		conn:        conn,
		log:         log.WithField("bindDN", bindDN).WithField("requestId", rid).WithField("client", utils.GetIP(conn.RemoteAddr())),
		id:          rid,
		ctx:         span.Context(),
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

func (r *Request) ID() string {
	return r.id
}
