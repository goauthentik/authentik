package direct

import (
	"context"
	"errors"
	"strings"

	"github.com/getsentry/sentry-go"
	goldap "github.com/go-ldap/ldap/v3"
	"github.com/nmcclain/ldap"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/ldap/bind"
	"goauthentik.io/internal/outpost/ldap/flags"
	"goauthentik.io/internal/outpost/ldap/metrics"
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

func (db *DirectBinder) Bind(username string, req *bind.Request) (ldap.LDAPResultCode, error) {
	fe := flow.NewFlowExecutor(req.Context(), db.si.GetFlowSlug(), db.si.GetAPIClient().GetConfig(), log.Fields{
		"bindDN":    req.BindDN,
		"client":    req.RemoteAddr(),
		"requestId": req.ID(),
	})
	fe.DelegateClientIP(req.RemoteAddr())
	fe.Params.Add("goauthentik.io/outpost/ldap", "true")

	fe.Answers[flow.StageIdentification] = username
	fe.Answers[flow.StagePassword] = req.BindPW

	passed, err := fe.Execute()
	flags := flags.UserFlags{
		Session: fe.GetSession(),
	}
	db.si.SetFlags(req.BindDN, flags)
	if !passed {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": db.si.GetOutpostName(),
			"type":         "bind",
			"reason":       "invalid_credentials",
			"app":          db.si.GetAppSlug(),
		}).Inc()
		req.Log().Info("Invalid credentials")
		return ldap.LDAPResultInvalidCredentials, nil
	}
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": db.si.GetOutpostName(),
			"type":         "bind",
			"reason":       "flow_error",
			"app":          db.si.GetAppSlug(),
		}).Inc()
		req.Log().WithError(err).Warning("failed to execute flow")
		return ldap.LDAPResultOperationsError, nil
	}

	access, err := fe.CheckApplicationAccess(db.si.GetAppSlug())
	if !access {
		req.Log().Info("Access denied for user")
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": db.si.GetOutpostName(),
			"type":         "bind",
			"reason":       "access_denied",
			"app":          db.si.GetAppSlug(),
		}).Inc()
		return ldap.LDAPResultInsufficientAccessRights, nil
	}
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": db.si.GetOutpostName(),
			"type":         "bind",
			"reason":       "access_check_fail",
			"app":          db.si.GetAppSlug(),
		}).Inc()
		req.Log().WithError(err).Warning("failed to check access")
		return ldap.LDAPResultOperationsError, nil
	}
	req.Log().Info("User has access")
	uisp := sentry.StartSpan(req.Context(), "authentik.providers.ldap.bind.user_info")
	// Get user info to store in context
	userInfo, _, err := fe.ApiClient().CoreApi.CoreUsersMeRetrieve(context.Background()).Execute()
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": db.si.GetOutpostName(),
			"type":         "bind",
			"reason":       "user_info_fail",
			"app":          db.si.GetAppSlug(),
		}).Inc()
		req.Log().WithError(err).Warning("failed to get user info")
		return ldap.LDAPResultOperationsError, nil
	}
	cs := db.SearchAccessCheck(userInfo.User)
	flags.UserPk = userInfo.User.Pk
	flags.CanSearch = cs != nil
	db.si.SetFlags(req.BindDN, flags)
	if flags.CanSearch {
		req.Log().WithField("group", cs).Info("Allowed access to search")
	}
	uisp.Finish()
	return ldap.LDAPResultSuccess, nil
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

func (db *DirectBinder) TimerFlowCacheExpiry() {
	fe := flow.NewFlowExecutor(context.Background(), db.si.GetFlowSlug(), db.si.GetAPIClient().GetConfig(), log.Fields{})
	fe.Params.Add("goauthentik.io/outpost/ldap", "true")
	fe.Params.Add("goauthentik.io/outpost/ldap-warmup", "true")

	err := fe.WarmUp()
	if err != nil {
		db.log.WithError(err).Warning("failed to warm up flow cache")
	}
}
