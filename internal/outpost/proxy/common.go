package proxy

import (
	"time"

	"github.com/oauth2-proxy/oauth2-proxy/pkg/apis/options"
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
	return commonOpts
}
