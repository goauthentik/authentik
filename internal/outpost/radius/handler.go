package radius

import (
	"crypto/sha512"
	"encoding/hex"
	"net"
	"time"

	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/outpost/radius/metrics"
	"layeh.com/radius"
	"layeh.com/radius/rfc2869"
)

type LogWriter struct {
	w radius.ResponseWriter
	l *log.Entry
}

func (lw LogWriter) Write(packet *radius.Packet) error {
	lw.l.WithField("code", packet.Code.String()).Info("Radius Response")
	return lw.w.Write(packet)
}

func (rs *RadiusServer) ServeRADIUS(w radius.ResponseWriter, r *radius.Request) {
	span := sentry.StartSpan(r.Context(), "authentik.providers.radius.connect",
		sentry.WithTransactionName("authentik.providers.radius.connect"))
	rid := uuid.New().String()
	span.SetTag("request_uid", rid)
	host, _, err := net.SplitHostPort(r.RemoteAddr.String())
	if err != nil {
		rs.log.WithError(err).Warning("Failed to get remote IP")
		return
	}
	rl := rs.log.WithFields(log.Fields{
		"code":    r.Code.String(),
		"request": rid,
		"ip":      host,
		"id":      r.Identifier,
	})
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

	if err := nr.validateMessageAuthenticator(); err != nil {
		rl.WithError(err).Warning("Invalid message authenticator")
		return
	}

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
		hs := sha512.Sum512([]byte(r.Secret))
		bs := hex.EncodeToString(hs[:])
		nr.Log().WithField("hashed_secret", bs).Warning("No provider found")
		_ = w.Write(nr.Reject())
		return
	}
	nr.pi = pi

	if nr.Code == radius.CodeAccessRequest {
		rs.Handle_AccessRequest(w, nr)
	}
}

func (rs *RadiusServer) Handle_AccessRequest(w radius.ResponseWriter, r *RadiusRequest) {
	eap := rfc2869.EAPMessage_Get(r.Packet)
	if len(eap) > 0 {
		rs.log.Trace("EAP request")
		rs.Handle_AccessRequest_EAP(w, r)
	} else {
		rs.log.Trace("PAP request")
		rs.Handle_AccessRequest_PAP(w, r)
	}
}
