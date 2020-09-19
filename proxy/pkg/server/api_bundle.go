package server

import (
	"context"
	"crypto/tls"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"

	"github.com/BeryJu/passbook/proxy/pkg/client/crypto"
	"github.com/BeryJu/passbook/proxy/pkg/models"
	"github.com/BeryJu/passbook/proxy/pkg/proxy"
	"github.com/jinzhu/copier"
	"github.com/justinas/alice"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/apis/options"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/middleware"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/validation"
	log "github.com/sirupsen/logrus"
)

type providerBundle struct {
	http.Handler

	a     *APIController
	proxy *proxy.OAuthProxy
	Host  string

	cert *tls.Certificate
}

func (pb *providerBundle) prepareOpts(provider *models.ProxyOutpostConfig) *options.Options {
	externalHost, err := url.Parse(*provider.ExternalHost)
	if err != nil {
		log.WithError(err).Warning("Failed to parse URL, skipping provider")
		return nil
	}
	providerOpts := &options.Options{}
	copier.Copy(&providerOpts, &pb.a.commonOpts)
	providerOpts.ClientID = provider.ClientID
	providerOpts.ClientSecret = provider.ClientSecret

	providerOpts.Cookie.Secret = provider.CookieSecret
	providerOpts.Cookie.Secure = externalHost.Scheme == "https"

	providerOpts.SkipOIDCDiscovery = true
	providerOpts.OIDCIssuerURL = *provider.OidcConfiguration.Issuer
	providerOpts.LoginURL = *provider.OidcConfiguration.AuthorizationEndpoint
	providerOpts.RedeemURL = *provider.OidcConfiguration.TokenEndpoint
	providerOpts.OIDCJwksURL = *provider.OidcConfiguration.JwksURI
	providerOpts.ProfileURL = *provider.OidcConfiguration.UserinfoEndpoint

	if provider.SkipPathRegex != "" {
		skipRegexes := strings.Split(provider.SkipPathRegex, "\n")
		providerOpts.SkipAuthRegex = skipRegexes
	}

	providerOpts.UpstreamServers = []options.Upstream{
		{
			ID:   "default",
			URI:  *provider.InternalHost,
			Path: "/",
		},
	}

	if provider.Certificate != nil {
		pb.a.logger.WithField("provider", provider.ClientID).Debug("Enabling TLS")
		cert, err := pb.a.client.Crypto.CryptoCertificatekeypairsRead(&crypto.CryptoCertificatekeypairsReadParams{
			Context: context.Background(),
			KpUUID:  *provider.Certificate,
		}, pb.a.auth)
		if err != nil {
			pb.a.logger.WithField("provider", provider.ClientID).WithError(err).Warning("Failed to fetch certificate")
			return providerOpts
		}
		x509cert, err := tls.X509KeyPair([]byte(*cert.Payload.CertificateData), []byte(cert.Payload.KeyData))
		if err != nil {
			pb.a.logger.WithField("provider", provider.ClientID).WithError(err).Warning("Failed to parse certificate")
			return providerOpts
		}
		pb.cert = &x509cert
		pb.a.logger.WithField("provider", provider.ClientID).WithField("certificate-key-pair", *cert.Payload.Name).Debug("Loaded certificates")
	}
	return providerOpts
}

func (pb *providerBundle) Build(provider *models.ProxyOutpostConfig) {
	opts := pb.prepareOpts(provider)

	chain := alice.New()

	if opts.ForceHTTPS {
		_, httpsPort, err := net.SplitHostPort(opts.HTTPSAddress)
		if err != nil {
			log.Fatalf("FATAL: invalid HTTPS address %q: %v", opts.HTTPAddress, err)
		}
		chain = chain.Append(middleware.NewRedirectToHTTPS(httpsPort))
	}

	healthCheckPaths := []string{opts.PingPath}
	healthCheckUserAgents := []string{opts.PingUserAgent}
	if opts.GCPHealthChecks {
		healthCheckPaths = append(healthCheckPaths, "/liveness_check", "/readiness_check")
		healthCheckUserAgents = append(healthCheckUserAgents, "GoogleHC/1.0")
	}

	// To silence logging of health checks, register the health check handler before
	// the logging handler
	if opts.Logging.SilencePing {
		chain = chain.Append(middleware.NewHealthCheck(healthCheckPaths, healthCheckUserAgents), LoggingHandler)
	} else {
		chain = chain.Append(LoggingHandler, middleware.NewHealthCheck(healthCheckPaths, healthCheckUserAgents))
	}

	err := validation.Validate(opts)
	if err != nil {
		log.Printf("%s", err)
		os.Exit(1)
	}
	oauthproxy, err := proxy.NewOAuthProxy(opts)
	if err != nil {
		log.Errorf("ERROR: Failed to initialise OAuth2 Proxy: %v", err)
		os.Exit(1)
	}

	pb.proxy = oauthproxy
	pb.Handler = chain.Then(oauthproxy)
}
