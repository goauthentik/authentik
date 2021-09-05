package proxy

import (
	"fmt"
	"time"

	log "github.com/sirupsen/logrus"

	"github.com/oauth2-proxy/oauth2-proxy/pkg/apis/options"
	"goauthentik.io/internal/config"
)

func getCommonOptions() *options.Options {
	commonOpts := options.NewOptions()
	commonOpts.Cookie.Name = "authentik_proxy"
	commonOpts.Cookie.Expire = 24 * time.Hour
	commonOpts.EmailDomains = []string{"*"}
	commonOpts.ProviderType = "oidc"
	commonOpts.ProxyPrefix = "/akprox"
	commonOpts.Logging.SilencePing = true
	commonOpts.SetAuthorization = false
	commonOpts.Scope = "openid email profile ak_proxy"
	if config.G.Redis.Host != "" {
		protocol := "redis"
		if config.G.Redis.TLS {
			protocol = "rediss"
		}
		url := fmt.Sprintf("%s://@%s:%d/%d", protocol, config.G.Redis.Host, config.G.Redis.Port, config.G.Redis.OutpostSessionDB)
		log.WithField("url", url).Info("Using redis session backend")
		commonOpts.Session.Redis = options.RedisStoreOptions{
			ConnectionURL: url,
			Password:      config.G.Redis.Password,
		}
		if config.G.Redis.TLSReqs != "" {
			commonOpts.Session.Redis.InsecureSkipTLSVerify = true
		}
	}
	return commonOpts
}
