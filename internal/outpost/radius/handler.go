package radius

import (
	"crypto/sha512"
	"time"

	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus"
	"go.uber.org/zap"

	"goauthentik.io/internal/outpost/radius/metrics"
	"goauthentik.io/internal/utils"
	"layeh.com/radius"
)

type RadiusRequest struct {
	*radius.Request
	log  *zap.Logger
	id   string
	span *sentry.Span
	pi   *ProviderInstance
}

func (r *RadiusRequest) Log() *zap.Logger {
	return r.log
}

func (r *RadiusRequest) RemoteAddr() string {
	return utils.GetIP(r.Request.RemoteAddr)
}

func (r *RadiusRequest) ID() string {
	return r.id
}

func (rs *RadiusServer) ServeRADIUS(w radius.ResponseWriter, r *radius.Request) {
	span := sentry.StartSpan(r.Context(), "authentik.providers.radius.connect",
		sentry.WithTransactionName("authentik.providers.radius.connect"))
	rid := uuid.New().String()
	span.SetTag("request_uid", rid)
	rl := rs.log.With(zap.String("code", r.Code.String()), zap.String("request", rid))
	selectedApp := ""
	defer func() {
		span.Finish()
		metrics.Requests.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"app":          selectedApp,
		}).Observe(float64(span.EndTime.Sub(span.StartTime)) / float64(time.Second))
	}()

	nr := &RadiusRequest{
		Request: r,
		log:     rl,
		id:      rid,
		span:    span,
	}

	rl.Info("Radius Request")

	// Lookup provider by shared secret
	var pi *ProviderInstance
	for _, p := range rs.providers {
		if string(p.SharedSecret) == string(r.Secret) {
			pi = p
			selectedApp = pi.appSlug
			break
		}
	}
	if pi == nil {
		nr.Log().Warn("No provider found", zap.String("hashed_secret", string(sha512.New().Sum(r.Secret))))
		_ = w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	nr.pi = pi

	if nr.Code == radius.CodeAccessRequest {
		rs.Handle_AccessRequest(w, nr)
	}
}
