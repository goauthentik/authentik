package outpost

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strconv"
	"strings"

	"github.com/getsentry/sentry-go"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ak"
)

type StageComponent string

const (
	StageIdentification        = StageComponent("ak-stage-identification")
	StagePassword              = StageComponent("ak-stage-password")
	StageAuthenticatorValidate = StageComponent("ak-stage-authenticator-validate")
	StageAccessDenied          = StageComponent("ak-stage-access-denied")
)

const (
	HeaderAuthentikRemoteIP     = "X-authentik-remote-ip"
	HeaderAuthentikOutpostToken = "X-authentik-outpost-token"
)

type FlowExecutor struct {
	Params  url.Values
	Answers map[StageComponent]string
	Context context.Context

	api      *api.APIClient
	flowSlug string
	log      *log.Entry
	token    string

	sp *sentry.Span
}

func NewFlowExecutor(ctx context.Context, flowSlug string, refConfig *api.Configuration, logFields log.Fields) *FlowExecutor {
	rsp := sentry.StartSpan(ctx, "authentik.outposts.flow_executor")

	l := log.WithField("flow", flowSlug).WithFields(logFields)
	jar, err := cookiejar.New(nil)
	if err != nil {
		l.WithError(err).Warning("Failed to create cookiejar")
		panic(err)
	}
	// Create new http client that also sets the correct ip
	config := api.NewConfiguration()
	config.Host = refConfig.Host
	config.Scheme = refConfig.Scheme
	config.UserAgent = constants.OutpostUserAgent()
	config.HTTPClient = &http.Client{
		Jar:       jar,
		Transport: ak.NewTracingTransport(ak.GetTLSTransport()),
	}
	apiClient := api.NewAPIClient(config)
	return &FlowExecutor{
		Params:   url.Values{},
		Answers:  make(map[StageComponent]string),
		Context:  rsp.Context(),
		api:      apiClient,
		flowSlug: flowSlug,
		log:      l,
		token:    strings.Split(refConfig.DefaultHeader["Authorization"], " ")[1],
		sp:       rsp,
	}
}

func (fe *FlowExecutor) ApiClient() *api.APIClient {
	return fe.api
}

type ChallengeInt interface {
	GetComponent() string
	GetType() api.ChallengeChoices
	GetResponseErrors() map[string][]api.ErrorDetail
}

func (fe *FlowExecutor) DelegateClientIP(a net.Addr) {
	host, _, err := net.SplitHostPort(a.String())
	if err != nil {
		fe.log.WithError(err).Warning("Failed to get remote IP")
		return
	}
	fe.api.GetConfig().AddDefaultHeader(HeaderAuthentikRemoteIP, host)
	fe.api.GetConfig().AddDefaultHeader(HeaderAuthentikOutpostToken, fe.token)
}

func (fe *FlowExecutor) CheckApplicationAccess(appSlug string) (bool, error) {
	acsp := sentry.StartSpan(fe.Context, "authentik.outposts.flow_executor.check_access")
	defer acsp.Finish()
	p, _, err := fe.api.CoreApi.CoreApplicationsCheckAccessRetrieve(acsp.Context(), appSlug).Execute()
	if !p.Passing {
		fe.log.Info("Access denied for user")
		return false, nil
	}
	if err != nil {
		return false, fmt.Errorf("failed to check access: %w", err)
	}
	fe.log.Debug("User has access")
	return true, nil
}

func (fe *FlowExecutor) getAnswer(stage StageComponent) string {
	if v, o := fe.Answers[stage]; o {
		return v
	}
	return ""
}

// WarmUp Ensure authentik's flow cache is warmed up
func (fe *FlowExecutor) WarmUp() error {
	defer fe.sp.Finish()
	gcsp := sentry.StartSpan(fe.Context, "authentik.outposts.flow_executor.get_challenge")
	req := fe.api.FlowsApi.FlowsExecutorGet(gcsp.Context(), fe.flowSlug).Query(fe.Params.Encode())
	_, _, err := req.Execute()
	return err
}

func (fe *FlowExecutor) Execute() (bool, error) {
	return fe.solveFlowChallenge(1)
}

func (fe *FlowExecutor) solveFlowChallenge(depth int) (bool, error) {
	defer fe.sp.Finish()

	// Get challenge
	gcsp := sentry.StartSpan(fe.Context, "authentik.outposts.flow_executor.get_challenge")
	req := fe.api.FlowsApi.FlowsExecutorGet(gcsp.Context(), fe.flowSlug).Query(fe.Params.Encode())
	challenge, _, err := req.Execute()
	if err != nil {
		return false, errors.New("failed to get challenge")
	}
	ch := challenge.GetActualInstance().(ChallengeInt)
	fe.log.WithField("component", ch.GetComponent()).WithField("type", ch.GetType()).Debug("Got challenge")
	gcsp.SetTag("ak_challenge", string(ch.GetType()))
	gcsp.SetTag("ak_component", ch.GetComponent())
	gcsp.Finish()

	// Resole challenge
	scsp := sentry.StartSpan(fe.Context, "authentik.outposts.flow_executor.solve_challenge")
	responseReq := fe.api.FlowsApi.FlowsExecutorSolve(scsp.Context(), fe.flowSlug).Query(fe.Params.Encode())
	switch ch.GetComponent() {
	case string(StageIdentification):
		responseReq = responseReq.FlowChallengeResponseRequest(api.IdentificationChallengeResponseRequestAsFlowChallengeResponseRequest(api.NewIdentificationChallengeResponseRequest(fe.getAnswer(StageIdentification))))
	case string(StagePassword):
		responseReq = responseReq.FlowChallengeResponseRequest(api.PasswordChallengeResponseRequestAsFlowChallengeResponseRequest(api.NewPasswordChallengeResponseRequest(fe.getAnswer(StagePassword))))
	case string(StageAuthenticatorValidate):
		// We only support duo as authenticator, check if that's allowed
		var deviceChallenge *api.DeviceChallenge
		for _, devCh := range challenge.AuthenticatorValidationChallenge.DeviceChallenges {
			if devCh.DeviceClass == string(api.DEVICECLASSESENUM_DUO) {
				deviceChallenge = &devCh
			}
		}
		if deviceChallenge == nil {
			return false, errors.New("got ak-stage-authenticator-validate without duo")
		}
		devId, err := strconv.Atoi(deviceChallenge.DeviceUid)
		if err != nil {
			return false, errors.New("failed to convert duo device id to int")
		}
		devId32 := int32(devId)
		inner := api.NewAuthenticatorValidationChallengeResponseRequest()
		inner.Duo = &devId32
		responseReq = responseReq.FlowChallengeResponseRequest(api.AuthenticatorValidationChallengeResponseRequestAsFlowChallengeResponseRequest(inner))
	case string(StageAccessDenied):
		return false, errors.New("got ak-stage-access-denied")
	default:
		return false, fmt.Errorf("unsupported challenge type %s", ch.GetComponent())
	}

	response, _, err := responseReq.Execute()
	ch = response.GetActualInstance().(ChallengeInt)
	fe.log.WithField("component", ch.GetComponent()).WithField("type", ch.GetType()).Debug("Got response")
	scsp.SetTag("ak_challenge", string(ch.GetType()))
	scsp.SetTag("ak_component", ch.GetComponent())
	scsp.Finish()

	switch ch.GetComponent() {
	case string(StageAccessDenied):
		return false, errors.New("got ak-stage-access-denied")
	}
	if ch.GetType() == "redirect" {
		return true, nil
	}
	if err != nil {
		return false, fmt.Errorf("failed to submit challenge %w", err)
	}
	if len(ch.GetResponseErrors()) > 0 {
		for key, errs := range ch.GetResponseErrors() {
			for _, err := range errs {
				return false, fmt.Errorf("flow error %s: %s", key, err.String)
			}
		}
	}
	if depth >= 10 {
		return false, errors.New("exceeded stage recursion depth")
	}
	return fe.solveFlowChallenge(depth + 1)
}
