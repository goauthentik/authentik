package direct

import (
	"beryju.io/ldap"
	"go.uber.org/zap"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/ldap/bind"
)

func (db *DirectBinder) Unbind(username string, req *bind.Request) (ldap.LDAPResultCode, error) {
	flowSlug := db.si.GetInvalidationFlowSlug()
	if flowSlug == nil {
		req.Log().Debug("Provider does not have a logout flow configured")
		db.si.SetFlags(req.BindDN, nil)
		return ldap.LDAPResultSuccess, nil
	}
	flags := db.si.GetFlags(req.BindDN)
	if flags == nil || flags.Session == nil {
		return ldap.LDAPResultSuccess, nil
	}
	fe := flow.NewFlowExecutor(req.Context(), *flowSlug, db.si.GetAPIClient().GetConfig(), []zap.Field{
		zap.String("boundDN", req.BindDN),
		zap.String("client", req.RemoteAddr()),
		zap.String("requestId", req.ID()),
	})
	fe.SetSession(flags.Session)
	fe.DelegateClientIP(req.RemoteAddr())
	fe.Params.Add("goauthentik.io/outpost/ldap", "true")
	_, err := fe.Execute()
	if err != nil {
		req.Log().Warn("failed to logout user", zap.Error(err))
	}
	db.si.SetFlags(req.BindDN, nil)
	return ldap.LDAPResultSuccess, nil
}
