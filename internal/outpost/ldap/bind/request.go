package bind

import (
	"context"
	"net"
	"strings"

	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/utils"
)

type Request struct {
	BindDN string
	BindPW string
	id     string
	conn   net.Conn
	log    *log.Entry
	ctx    context.Context
}

func NewRequest(bindDN string, bindPW string, conn net.Conn) (*Request, *sentry.Span) {
	span := sentry.StartSpan(context.TODO(), "authentik.providers.ldap.bind",
		sentry.TransactionName("authentik.providers.ldap.bind"))
	rid := uuid.New().String()
	span.SetTag("request_uid", rid)
	span.SetTag("user.username", bindDN)

	bindDN = strings.ToLower(bindDN)
	return &Request{
		BindDN: bindDN,
		BindPW: bindPW,
		conn:   conn,
		log:    log.WithField("bindDN", bindDN).WithField("requestId", rid).WithField("client", utils.GetIP(conn.RemoteAddr())),
		id:     rid,
		ctx:    span.Context(),
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
