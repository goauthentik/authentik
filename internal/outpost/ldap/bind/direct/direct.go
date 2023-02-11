package direct

import (
	"context"
	"errors"
	"strings"

	goldap "github.com/go-ldap/ldap/v3"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/ldap/server"
	"goauthentik.io/internal/outpost/ldap/utils"
)

const ContextUserKey = "ak_user"

type DirectBinder struct {
	si  server.LDAPServerInstance
	log *log.Entry
}

func NewDirectBinder(si server.LDAPServerInstance) *DirectBinder {
	db := &DirectBinder{
		si:  si,
		log: log.WithField("logger", "authentik.outpost.ldap.binder.direct"),
	}
	db.log.Info("initialised direct binder")
	return db
}

func (db *DirectBinder) GetUsername(dn string) (string, error) {
	if !utils.HasSuffixNoCase(dn, db.si.GetBaseDN()) {
		return "", errors.New("invalid base DN")
	}
	dns, err := goldap.ParseDN(dn)
	if err != nil {
		return "", err
	}
	for _, part := range dns.RDNs {
		for _, attribute := range part.Attributes {
			if strings.ToLower(attribute.Type) == "cn" {
				return attribute.Value, nil
			}
		}
	}
	return "", errors.New("failed to find cn")
}

// SearchAccessCheck Check if the current user is allowed to search
func (db *DirectBinder) SearchAccessCheck(user api.UserSelf) *string {
	for _, group := range user.Groups {
		for _, allowedGroup := range db.si.GetSearchAllowedGroups() {
			if allowedGroup == nil {
				continue
			}
			db.log.WithField("userGroup", group.Pk).WithField("allowedGroup", allowedGroup).Trace("Checking search access")
			if group.Pk == allowedGroup.String() {
				return &group.Name
			}
		}
	}
	return nil
}

func (db *DirectBinder) TimerFlowCacheExpiry(ctx context.Context) {
	fe := flow.NewFlowExecutor(ctx, db.si.GetAuthenticationFlowSlug(), db.si.GetAPIClient().GetConfig(), log.Fields{})
	fe.Params.Add("goauthentik.io/outpost/ldap", "true")
	fe.Params.Add("goauthentik.io/outpost/ldap-warmup", "true")

	err := fe.WarmUp()
	if err != nil {
		db.log.WithError(err).Warning("failed to warm up flow cache")
	}
}
