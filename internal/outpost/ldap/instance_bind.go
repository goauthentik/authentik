package ldap

import (
	"context"
	"errors"
	"net"
	"strings"
	"time"

	goldap "github.com/go-ldap/ldap/v3"
	"github.com/nmcclain/ldap"
	"goauthentik.io/api"
	"goauthentik.io/internal/outpost"
)

const ContextUserKey = "ak_user"

func (pi *ProviderInstance) getUsername(dn string) (string, error) {
	if !strings.HasSuffix(strings.ToLower(dn), strings.ToLower(pi.BaseDN)) {
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

func (pi *ProviderInstance) Bind(username string, bindDN, bindPW string, conn net.Conn) (ldap.LDAPResultCode, error) {
	host, _, err := net.SplitHostPort(conn.RemoteAddr().String())
	if err != nil {
		pi.log.WithError(err).Warning("Failed to get remote IP")
		return ldap.LDAPResultOperationsError, nil
	}

	fe := outpost.NewFlowExecutor(pi.flowSlug, pi.s.ac.Client.GetConfig())
	fe.ApiClient().GetConfig().AddDefaultHeader("X-authentik-remote-ip", host)
	fe.Params.Add("goauthentik.io/outpost/ldap", "true")

	fe.Answers[outpost.StageIdentification] = username
	fe.Answers[outpost.StagePassword] = bindPW

	passed, err := fe.Execute()
	if err != nil {
		pi.log.WithField("bindDN", bindDN).WithError(err).Warning("failed to execute flow")
		return ldap.LDAPResultOperationsError, nil
	}
	if !passed {
		return ldap.LDAPResultInvalidCredentials, nil
	}
	access, err := fe.CheckApplicationAccess(pi.appSlug)
	if !access {
		pi.log.WithField("bindDN", bindDN).Info("Access denied for user")
		return ldap.LDAPResultInsufficientAccessRights, nil
	}
	if err != nil {
		pi.log.WithField("bindDN", bindDN).WithError(err).Warning("failed to check access")
		return ldap.LDAPResultOperationsError, nil
	}
	pi.log.WithField("bindDN", bindDN).Info("User has access")
	// Get user info to store in context
	userInfo, _, err := fe.ApiClient().CoreApi.CoreUsersMeRetrieve(context.Background()).Execute()
	if err != nil {
		pi.log.WithField("bindDN", bindDN).WithError(err).Warning("failed to get user info")
		return ldap.LDAPResultOperationsError, nil
	}
	pi.boundUsersMutex.Lock()
	pi.boundUsers[bindDN] = UserFlags{
		UserInfo:  userInfo.User,
		CanSearch: pi.SearchAccessCheck(userInfo.User),
	}
	defer pi.boundUsersMutex.Unlock()
	pi.delayDeleteUserInfo(username)
	return ldap.LDAPResultSuccess, nil
}

// SearchAccessCheck Check if the current user is allowed to search
func (pi *ProviderInstance) SearchAccessCheck(user api.User) bool {
	for _, group := range user.Groups {
		for _, allowedGroup := range pi.searchAllowedGroups {
			pi.log.WithField("userGroup", group.Pk).WithField("allowedGroup", allowedGroup).Trace("Checking search access")
			if group.Pk == allowedGroup.String() {
				pi.log.WithField("group", group.Name).Info("Allowed access to search")
				return true
			}
		}
	}
	return false
}

func (pi *ProviderInstance) delayDeleteUserInfo(dn string) {
	ticker := time.NewTicker(30 * time.Second)
	quit := make(chan struct{})
	go func() {
		for {
			select {
			case <-ticker.C:
				pi.boundUsersMutex.Lock()
				delete(pi.boundUsers, dn)
				pi.boundUsersMutex.Unlock()
				close(quit)
			case <-quit:
				ticker.Stop()
				return
			}
		}
	}()
}
