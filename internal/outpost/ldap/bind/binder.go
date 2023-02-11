package bind

import (
	"context"

	"github.com/nmcclain/ldap"
)

type Binder interface {
	GetUsername(string) (string, error)
	Bind(username string, req *Request) (ldap.LDAPResultCode, error)
	Unbind(username string, req *Request) (ldap.LDAPResultCode, error)
	TimerFlowCacheExpiry(context.Context)
}
