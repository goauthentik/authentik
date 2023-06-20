package direct

import (
	"context"
	"regexp"
	"strconv"
	"strings"

	"beryju.io/ldap"
	"github.com/getsentry/sentry-go"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/ldap/bind"
	"goauthentik.io/internal/outpost/ldap/flags"
	"goauthentik.io/internal/outpost/ldap/metrics"
)

const CodePasswordSeparator = ";"

var alphaNum = regexp.MustCompile(`^[a-zA-Z0-9]*$`)

func (db *DirectBinder) Bind(username string, req *bind.Request) (ldap.LDAPResultCode, error) {
	fe := flow.NewFlowExecutor(req.Context(), db.si.GetAuthenticationFlowSlug(), db.si.GetAPIClient().GetConfig(), log.Fields{
		"bindDN":    req.BindDN,
		"client":    req.RemoteAddr(),
		"requestId": req.ID(),
	})
	fe.DelegateClientIP(req.RemoteAddr())
	fe.Params.Add("goauthentik.io/outpost/ldap", "true")

	fe.Answers[flow.StageIdentification] = username
	fe.Answers[flow.StagePassword] = req.BindPW
	db.CheckPasswordMFA(fe)

	passed, err := fe.Execute()
	flags := flags.UserFlags{
		Session: fe.GetSession(),
	}
	db.si.SetFlags(req.BindDN, &flags)
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": db.si.GetOutpostName(),
			"type":         "bind",
			"reason":       "flow_error",
			"app":          db.si.GetAppSlug(),
		}).Inc()
		req.Log().WithError(err).Warning("failed to execute flow")
		return ldap.LDAPResultInvalidCredentials, nil
	}
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
	db.si.SetFlags(req.BindDN, &flags)
	if flags.CanSearch {
		req.Log().WithField("group", cs).Info("Allowed access to search")
	}
	uisp.Finish()
	return ldap.LDAPResultSuccess, nil
}

func (db *DirectBinder) CheckPasswordMFA(fe *flow.FlowExecutor) {
	if !db.si.GetMFASupport() {
		return
	}
	password := fe.Answers[flow.StagePassword]
	// We already have an authenticator answer
	if fe.Answers[flow.StageAuthenticatorValidate] != "" {
		return
	}
	// password doesn't contain the separator
	if !strings.Contains(password, CodePasswordSeparator) {
		return
	}
	// password ends with the separator, so it won't contain an answer
	if strings.HasSuffix(password, CodePasswordSeparator) {
		return
	}
	idx := strings.LastIndex(password, CodePasswordSeparator)
	authenticator := password[idx+1:]
	// Authenticator is either 6 chars (totp code) or 8 chars (long totp or static)
	if len(authenticator) == 6 {
		// authenticator answer isn't purely numerical, so won't be value
		if _, err := strconv.Atoi(authenticator); err != nil {
			return
		}
	} else if len(authenticator) == 8 {
		// 8 chars can be a long totp or static token, so it needs to be alphanumerical
		if !alphaNum.MatchString(authenticator) {
			return
		}
	} else {
		// Any other length, doesn't contain an answer
		return
	}
	fe.Answers[flow.StagePassword] = password[:idx]
	fe.Answers[flow.StageAuthenticatorValidate] = authenticator
}
