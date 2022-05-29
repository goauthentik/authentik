package flow

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strconv"
	"strings"

	"github.com/getsentry/sentry-go"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ak"
)

var (
	FlowTimingGet = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_flow_timing_get",
		Help: "Duration it took to get a challenge",
	}, []string{"stage", "flow"})
	FlowTimingPost = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_flow_timing_post",
		Help: "Duration it took to send a challenge",
	}, []string{"stage", "flow"})
)

type FlowExecutor struct {
	Params  url.Values
	Answers map[StageComponent]string
	Context context.Context

	cip       string
	api       *api.APIClient
	flowSlug  string
	log       *log.Entry
	token     string
	session   *http.Cookie
	transport http.RoundTripper

	sp *sentry.Span
}

func NewFlowExecutor(ctx context.Context, flowSlug string, refConfig *api.Configuration, logFields log.Fields) *FlowExecutor {
	rsp := sentry.StartSpan(ctx, "authentik.outposts.flow_executor")
	rsp.Description = flowSlug

	l := log.WithField("flow", flowSlug).WithFields(logFields)
	jar, err := cookiejar.New(nil)
	if err != nil {
		l.WithError(err).Warning("Failed to create cookiejar")
		panic(err)
	}
	transport := ak.NewUserAgentTransport(constants.OutpostUserAgent(), ak.NewTracingTransport(rsp.Context(), ak.GetTLSTransport()))
	fe := &FlowExecutor{
		Params:    url.Values{},
		Answers:   make(map[StageComponent]string),
		Context:   rsp.Context(),
		flowSlug:  flowSlug,
		log:       l,
		sp:        rsp,
		cip:       "",
		transport: transport,
	}
	// Create new http client that also sets the correct ip
	config := api.NewConfiguration()
	config.Host = refConfig.Host
	config.Scheme = refConfig.Scheme
	config.HTTPClient = &http.Client{
		Jar:       jar,
		Transport: fe,
	}
	fe.token = strings.Split(refConfig.DefaultHeader["Authorization"], " ")[1]
	config.AddDefaultHeader(HeaderAuthentikOutpostToken, fe.token)
	fe.api = api.NewAPIClient(config)
	return fe
}

func (fe *FlowExecutor) RoundTrip(req *http.Request) (*http.Response, error) {
	res, err := fe.transport.RoundTrip(req)
	if res != nil {
		for _, cookie := range res.Cookies() {
			if cookie.Name == "authentik_session" {
				fe.session = cookie
			}
		}
	}
	return res, err
}

func (fe *FlowExecutor) ApiClient() *api.APIClient {
	return fe.api
}

type ChallengeInt interface {
	GetComponent() string
	GetType() api.ChallengeChoices
	GetResponseErrors() map[string][]api.ErrorDetail
}

func (fe *FlowExecutor) DelegateClientIP(a string) {
	fe.cip = a
	fe.api.GetConfig().AddDefaultHeader(HeaderAuthentikRemoteIP, fe.cip)
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

func (fe *FlowExecutor) GetSession() *http.Cookie {
	return fe.session
}

// WarmUp Ensure authentik's flow cache is warmed up
func (fe *FlowExecutor) WarmUp() error {
	gcsp := sentry.StartSpan(fe.Context, "authentik.outposts.flow_executor.get_challenge")
	defer gcsp.Finish()
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
	gcsp.SetTag("authentik.flow.challenge", string(ch.GetType()))
	gcsp.SetTag("authentik.flow.component", ch.GetComponent())
	gcsp.Finish()
	FlowTimingGet.With(prometheus.Labels{
		"stage": ch.GetComponent(),
		"flow":  fe.flowSlug,
	}).Observe(float64(gcsp.EndTime.Sub(gcsp.StartTime)))

	// Resole challenge
	scsp := sentry.StartSpan(fe.Context, "authentik.outposts.flow_executor.solve_challenge")
	responseReq := fe.api.FlowsApi.FlowsExecutorSolve(scsp.Context(), fe.flowSlug).Query(fe.Params.Encode())
	switch ch.GetComponent() {
	case string(StageIdentification):
		r := api.NewIdentificationChallengeResponseRequest(fe.getAnswer(StageIdentification))
		r.SetPassword(fe.getAnswer(StagePassword))
		responseReq = responseReq.FlowChallengeResponseRequest(api.IdentificationChallengeResponseRequestAsFlowChallengeResponseRequest(r))
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
			return false, errors.New("no compatible authenticator class found")
		}
		devId, err := strconv.Atoi(deviceChallenge.DeviceUid)
		if err != nil {
			return false, errors.New("failed to convert duo device id to int")
		}
		devId32 := int32(devId)
		inner := api.NewAuthenticatorValidationChallengeResponseRequest()
		inner.SelectedChallenge = (*api.DeviceChallengeRequest)(deviceChallenge)
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
	scsp.SetTag("authentik.flow.challenge", string(ch.GetType()))
	scsp.SetTag("authentik.flow.component", ch.GetComponent())
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
	FlowTimingPost.With(prometheus.Labels{
		"stage": ch.GetComponent(),
		"flow":  fe.flowSlug,
	}).Observe(float64(scsp.EndTime.Sub(scsp.StartTime)))

	if depth >= 10 {
		return false, errors.New("exceeded stage recursion depth")
	}
	return fe.solveFlowChallenge(depth + 1)
}
