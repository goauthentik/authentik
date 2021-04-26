package ldap

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/http/cookiejar"
	"strings"

	goldap "github.com/go-ldap/ldap/v3"
	httptransport "github.com/go-openapi/runtime/client"

	"github.com/nmcclain/ldap"
	"goauthentik.io/outpost/pkg/client/core"
	"goauthentik.io/outpost/pkg/client/flows"
)

type UIDResponse struct {
	UIDFIeld string `json:"uid_field"`
}

type PasswordResponse struct {
	Password string `json:"password"`
}

func (ls *LDAPServer) getUsername(dn string) (string, error) {
	if !strings.HasSuffix(dn, ls.BaseDN) {
		return "", errors.New("invalid base DN")
	}
	dns, err := goldap.ParseDN(dn)
	if err != nil {
		return "", err
	}
	for _, part := range dns.RDNs {
		for _, attribute := range part.Attributes {
			if attribute.Type == "DN" {
				return attribute.Value, nil
			}
		}
	}
	return "", errors.New("failed to find dn")
}

func (ls *LDAPServer) Bind(bindDN string, bindPW string, conn net.Conn) (ldap.LDAPResultCode, error) {
	username, err := ls.getUsername(bindDN)
	if err != nil {
		ls.log.WithError(err).Warning("failed to parse user dn")
		return ldap.LDAPResultInvalidCredentials, nil
	}
	ls.log.WithField("dn", username).Debug("bind")
	jar, err := cookiejar.New(nil)
	if err != nil {
		ls.log.WithError(err).Warning("Failed to create cookiejar")
		return ldap.LDAPResultOperationsError, nil
	}
	client := &http.Client{
		Jar: jar,
	}
	passed, err := ls.solveFlowChallenge(username, bindPW, client)
	if err != nil {
		ls.log.WithField("dn", username).WithError(err).Warning("failed to solve challenge")
		return ldap.LDAPResultOperationsError, nil
	}
	if !passed {
		return ldap.LDAPResultInvalidCredentials, nil
	}
	_, err = ls.ac.Client.Core.CoreApplicationsCheckAccess(&core.CoreApplicationsCheckAccessParams{
		Slug:       ls.appSlug,
		Context:    context.Background(),
		HTTPClient: client,
	}, httptransport.PassThroughAuth)
	if err != nil {
		if _, denied := err.(*core.CoreApplicationsCheckAccessForbidden); denied {
			ls.log.WithField("dn", username).Info("Access denied for user")
			return ldap.LDAPResultInvalidCredentials, nil
		}
		ls.log.WithField("dn", username).WithError(err).Warning("failed to check access")
		return ldap.LDAPResultOperationsError, nil
	}
	ls.log.WithField("dn", username).Info("User has access")
	return ldap.LDAPResultSuccess, nil
}

func (ls *LDAPServer) solveFlowChallenge(bindDN string, password string, client *http.Client) (bool, error) {
	challenge, err := ls.ac.Client.Flows.FlowsExecutorGet(&flows.FlowsExecutorGetParams{
		FlowSlug:   ls.flowSlug,
		Query:      "ldap=true",
		Context:    context.Background(),
		HTTPClient: client,
	}, httptransport.PassThroughAuth)
	if err != nil {
		ls.log.WithError(err).Warning("Failed to get challenge")
		return false, err
	}
	ls.log.WithField("component", challenge.Payload.Component).WithField("type", *challenge.Payload.Type).Debug("Got challenge")
	responseParams := &flows.FlowsExecutorSolveParams{
		FlowSlug:   ls.flowSlug,
		Query:      "ldap=true",
		Context:    context.Background(),
		HTTPClient: client,
	}
	switch challenge.Payload.Component {
	case "ak-stage-identification":
		responseParams.Data = &UIDResponse{UIDFIeld: bindDN}
	case "ak-stage-password":
		responseParams.Data = &PasswordResponse{Password: password}
	default:
		return false, fmt.Errorf("unsupported challenge type: %s", challenge.Payload.Component)
	}
	response, err := ls.ac.Client.Flows.FlowsExecutorSolve(responseParams, httptransport.PassThroughAuth)
	ls.log.WithField("component", response.Payload.Component).WithField("type", *response.Payload.Type).Debug("Got response")
	if *response.Payload.Type == "redirect" {
		return true, nil
	}
	if err != nil {
		ls.log.WithError(err).Warning("Failed to submit challenge")
		return false, err
	}
	if len(response.Payload.ResponseErrors) > 0 {
		for key, errs := range response.Payload.ResponseErrors {
			for _, err := range errs {
				ls.log.WithField("key", key).WithField("code", *err.Code).Debug(*err.String)
				return false, nil
			}
		}
	}
	return ls.solveFlowChallenge(bindDN, password, client)
}
