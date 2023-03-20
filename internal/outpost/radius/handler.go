package radius

import (
	"crypto/sha512"

	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/outpost/radius/metrics"
	"layeh.com/radius"
)

type RadiusRequest struct {
	*radius.Request
	Log  *log.Entry
	ID   string
	span *sentry.Span
	pi   *ProviderInstance
}

func (rs *RadiusServer) ServeRADIUS(w radius.ResponseWriter, r *radius.Request) {
	span := sentry.StartSpan(r.Context(), "authentik.providers.radius.connect",
		sentry.TransactionName("authentik.providers.radius.connect"))
	rid := uuid.New().String()
	span.SetTag("request_uid", rid)
	rl := rs.log.WithField("code", r.Code.String()).WithField("request", rid)
	selectedApp := ""
	defer func() {
		span.Finish()
		metrics.Requests.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"app":          selectedApp,
		}).Observe(float64(span.EndTime.Sub(span.StartTime)))
	}()

	nr := &RadiusRequest{
		Request: r,
		Log:     rl,
		ID:      rid,
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
		nr.Log.WithField("hashed_secret", string(sha512.New().Sum(r.Secret))).Warning("No provider found")
		_ = w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	nr.pi = pi

	if nr.Code == radius.CodeAccessRequest {
		rs.Handle_AccessRequest(w, nr)
	}
}
