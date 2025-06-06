package application

type ProxyClaims struct {
	UserAttributes  map[string]interface{} `json:"user_attributes"`
	BackendOverride string                 `json:"backend_override"`
	HostHeader      string                 `json:"host_header"`
	IsSuperuser     bool                   `json:"is_superuser"`
}

type Claims struct {
	Sub               string       `json:"sub"`
	Exp               int          `json:"exp"`
	Email             string       `json:"email"`
	Verified          bool         `json:"email_verified"`
	Name              string       `json:"name"`
	PreferredUsername string       `json:"preferred_username"`
	Groups            []string     `json:"groups"`
	Entitlements      []string     `json:"entitlements"`
	Sid               string       `json:"sid"`
	Proxy             *ProxyClaims `json:"ak_proxy"`

	RawToken string
}
