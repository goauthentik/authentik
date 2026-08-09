package bind

import (
	"context"

	"beryju.io/ldap"
)

type Binder interface {
	GetUsername(dn string) (string, error)
	Bind(username string, req *Request) (ldap.LDAPResultCode, error)
	Unbind(username string, req *Request) (ldap.LDAPResultCode, error)
	TimerFlowCacheExpiry(context.Context)
}
