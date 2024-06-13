package application

type ProxyClaims struct {
	UserAttributes  map[string]interface{} `json:"user_attributes"`
	BackendOverride string                 `json:"backend_override"`
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
	Sid               string       `json:"sid"`
	Proxy             *ProxyClaims `json:"ak_proxy"`

	RawToken string
}
