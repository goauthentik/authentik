package direct

import (
	"beryju.io/ldap"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/ldap/bind"
)

func (db *DirectBinder) Unbind(username string, req *bind.Request) (ldap.LDAPResultCode, error) {
	flags := db.si.GetFlags(req.BindDN)
	if flags == nil || flags.Session == nil {
		return ldap.LDAPResultSuccess, nil
	}
	fe := flow.NewFlowExecutor(req.Context(), db.si.GetInvalidationFlowSlug(), db.si.GetAPIClient().GetConfig(), log.Fields{
		"boundDN":   req.BindDN,
		"client":    req.RemoteAddr(),
		"requestId": req.ID(),
	})
	fe.SetSession(flags.Session)
	fe.DelegateClientIP(req.RemoteAddr())
	fe.Params.Add("goauthentik.io/outpost/ldap", "true")
	_, err := fe.Execute()
	if err != nil {
		db.log.WithError(err).Warning("failed to logout user")
	}
	db.si.SetFlags(req.BindDN, nil)
	return ldap.LDAPResultSuccess, nil
}
