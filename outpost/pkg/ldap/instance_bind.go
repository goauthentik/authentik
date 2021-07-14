package ldap

import (
	"context"
	"errors"
	"net"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strconv"
	"strings"
	"time"

	goldap "github.com/go-ldap/ldap/v3"
	"github.com/nmcclain/ldap"
	"goauthentik.io/outpost/api"
	"goauthentik.io/outpost/pkg"
	"goauthentik.io/outpost/pkg/ak"
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
	jar, err := cookiejar.New(nil)
	if err != nil {
		pi.log.WithError(err).Warning("Failed to create cookiejar")
		return ldap.LDAPResultOperationsError, nil
	}
	host, _, err := net.SplitHostPort(conn.RemoteAddr().String())
	if err != nil {
		pi.log.WithError(err).Warning("Failed to get remote IP")
		return ldap.LDAPResultOperationsError, nil
	}

	// Create new http client that also sets the correct ip
	config := api.NewConfiguration()
	config.Host = pi.s.ac.Client.GetConfig().Host
	config.Scheme = pi.s.ac.Client.GetConfig().Scheme
	config.UserAgent = pkg.UserAgent()
	config.HTTPClient = &http.Client{
		Jar:       jar,
		Transport: ak.GetTLSTransport(),
	}
	config.AddDefaultHeader("X-authentik-remote-ip", host)
	// create the API client, with the transport
	apiClient := api.NewAPIClient(config)

	params := url.Values{}
	params.Add("goauthentik.io/outpost/ldap", "true")
	passed, rerr := pi.solveFlowChallenge(username, bindPW, apiClient, params.Encode(), 1)
	if rerr != ldap.LDAPResultSuccess {
		pi.log.WithField("bindDN", bindDN).WithError(err).Warning("failed to solve challenge")
		return rerr, nil
	}
	if !passed {
		return ldap.LDAPResultInvalidCredentials, nil
	}
	p, _, err := apiClient.CoreApi.CoreApplicationsCheckAccessRetrieve(context.Background(), pi.appSlug).Execute()
	if !p.Passing {
		pi.log.WithField("bindDN", bindDN).Info("Access denied for user")
		return ldap.LDAPResultInsufficientAccessRights, nil
	}
	if err != nil {
		pi.log.WithField("bindDN", bindDN).WithError(err).Warning("failed to check access")
		return ldap.LDAPResultOperationsError, nil
	}
	pi.log.WithField("bindDN", bindDN).Info("User has access")
	// Get user info to store in context
	userInfo, _, err := apiClient.CoreApi.CoreUsersMeRetrieve(context.Background()).Execute()
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

type ChallengeInt interface {
	GetComponent() string
	GetType() api.ChallengeChoices
	GetResponseErrors() map[string][]api.ErrorDetail
}

func (pi *ProviderInstance) solveFlowChallenge(bindDN string, password string, client *api.APIClient, urlParams string, depth int) (bool, ldap.LDAPResultCode) {
	req := client.FlowsApi.FlowsExecutorGet(context.Background(), pi.flowSlug).Query(urlParams)
	challenge, _, err := req.Execute()
	if err != nil {
		pi.log.WithError(err).Warning("Failed to get challenge")
		return false, ldap.LDAPResultOperationsError
	}
	ch := challenge.GetActualInstance().(ChallengeInt)
	pi.log.WithField("component", ch.GetComponent()).WithField("type", ch.GetType()).Debug("Got challenge")
	responseReq := client.FlowsApi.FlowsExecutorSolve(context.Background(), pi.flowSlug).Query(urlParams)
	switch ch.GetComponent() {
	case "ak-stage-identification":
		responseReq = responseReq.FlowChallengeResponseRequest(api.IdentificationChallengeResponseRequestAsFlowChallengeResponseRequest(api.NewIdentificationChallengeResponseRequest(bindDN)))
	case "ak-stage-password":
		responseReq = responseReq.FlowChallengeResponseRequest(api.PasswordChallengeResponseRequestAsFlowChallengeResponseRequest(api.NewPasswordChallengeResponseRequest(password)))
	case "ak-stage-authenticator-validate":
		// We only support duo as authenticator, check if that's allowed
		var deviceChallenge *api.DeviceChallenge
		for _, devCh := range challenge.AuthenticatorValidationChallenge.DeviceChallenges {
			if devCh.DeviceClass == string(api.DEVICECLASSESENUM_DUO) {
				deviceChallenge = &devCh
			}
		}
		if deviceChallenge == nil {
			pi.log.Warning("got ak-stage-authenticator-validate without duo")
			return false, ldap.LDAPResultOperationsError
		}
		devId, err := strconv.Atoi(deviceChallenge.DeviceUid)
		if err != nil {
			pi.log.Warning("failed to convert duo device id to int")
			return false, ldap.LDAPResultOperationsError
		}
		devId32 := int32(devId)
		inner := api.NewAuthenticatorValidationChallengeResponseRequest()
		inner.Duo = &devId32
		responseReq = responseReq.FlowChallengeResponseRequest(api.AuthenticatorValidationChallengeResponseRequestAsFlowChallengeResponseRequest(inner))
	case "ak-stage-access-denied":
		pi.log.Info("got ak-stage-access-denied")
		return false, ldap.LDAPResultInsufficientAccessRights
	default:
		pi.log.WithField("component", ch.GetComponent()).Warning("unsupported challenge type")
		return false, ldap.LDAPResultOperationsError
	}
	response, _, err := responseReq.Execute()
	ch = response.GetActualInstance().(ChallengeInt)
	pi.log.WithField("component", ch.GetComponent()).WithField("type", ch.GetType()).Debug("Got response")
	switch ch.GetComponent() {
	case "ak-stage-access-denied":
		pi.log.Info("got ak-stage-access-denied")
		return false, ldap.LDAPResultInsufficientAccessRights
	}
	if ch.GetType() == "redirect" {
		return true, ldap.LDAPResultSuccess
	}
	if err != nil {
		pi.log.WithError(err).Warning("Failed to submit challenge")
		return false, ldap.LDAPResultOperationsError
	}
	if len(ch.GetResponseErrors()) > 0 {
		for key, errs := range ch.GetResponseErrors() {
			for _, err := range errs {
				pi.log.WithField("key", key).WithField("code", err.Code).WithField("msg", err.String).Warning("Flow error")
				return false, ldap.LDAPResultInsufficientAccessRights
			}
		}
	}
	if depth >= 10 {
		pi.log.Warning("exceeded stage recursion depth")
		return false, ldap.LDAPResultOperationsError
	}
	return pi.solveFlowChallenge(bindDN, password, client, urlParams, depth+1)
}
