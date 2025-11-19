package types

type ProxyClaims struct {
	UserAttributes  map[string]any `json:"user_attributes" mapstructure:"user_attributes"`
	BackendOverride string         `json:"backend_override" mapstructure:"backend_override"`
	HostHeader      string         `json:"host_header" mapstructure:"host_header"`
	IsSuperuser     bool           `json:"is_superuser" mapstructure:"is_superuser"`
}

type Claims struct {
	Sub               string       `json:"sub" mapstructure:"sub"`
	Exp               int          `json:"exp" mapstructure:"exp"`
	Email             string       `json:"email" mapstructure:"email"`
	Verified          bool         `json:"email_verified" mapstructure:"email_verified"`
	Name              string       `json:"name" mapstructure:"name"`
	PreferredUsername string       `json:"preferred_username" mapstructure:"preferred_username"`
	Groups            []string     `json:"groups" mapstructure:"groups"`
	Entitlements      []string     `json:"entitlements" mapstructure:"entitlements"`
	Sid               string       `json:"sid" mapstructure:"sid"`
	Proxy             *ProxyClaims `json:"ak_proxy" mapstructure:"ak_proxy"`

	RawToken string `json:"raw_token" mapstructure:"raw_token"`
}
