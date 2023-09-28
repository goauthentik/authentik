package flow

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strings"
	"time"

	"github.com/getsentry/sentry-go"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/utils/web"
)

var (
	FlowTimingGet = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_flow_timing_get_seconds",
		Help: "Duration it took to get a challenge in seconds",
	}, []string{"stage", "flow"})
	FlowTimingPost = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_flow_timing_post_seconds",
		Help: "Duration it took to send a challenge in seconds",
	}, []string{"stage", "flow"})

	// NOTE: the following metrics are kept for compatibility purpose
	FlowTimingGetLegacy = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_flow_timing_get",
		Help: "Duration it took to get a challenge",
	}, []string{"stage", "flow"})
	FlowTimingPostLegacy = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_flow_timing_post",
		Help: "Duration it took to send a challenge",
	}, []string{"stage", "flow"})
)

type SolverFunction func(*api.ChallengeTypes, api.ApiFlowsExecutorSolveRequest) (api.FlowChallengeResponseRequest, error)

type FlowExecutor struct {
	Params  url.Values
	Answers map[StageComponent]string
	Context context.Context

	solvers map[StageComponent]SolverFunction

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
	transport := web.NewUserAgentTransport(constants.OutpostUserAgent(), web.NewTracingTransport(rsp.Context(), ak.GetTLSTransport()))
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
	fe.solvers = map[StageComponent]SolverFunction{
		StageIdentification:        fe.solveChallenge_Identification,
		StagePassword:              fe.solveChallenge_Password,
		StageAuthenticatorValidate: fe.solveChallenge_AuthenticatorValidate,
		StageUserLogin:             fe.solveChallenge_UserLogin,
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

type challengeInt interface {
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
	if err != nil {
		return false, fmt.Errorf("failed to check access: %w", err)
	}
	if !p.Passing {
		fe.log.Info("Access denied for user")
		return false, nil
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

func (fe *FlowExecutor) SetSession(s *http.Cookie) {
	fe.session = s
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
	initial, err := fe.getInitialChallenge()
	if err != nil {
		return false, err
	}
	defer fe.sp.Finish()
	return fe.solveFlowChallenge(initial, 1)
}

func (fe *FlowExecutor) getInitialChallenge() (*api.ChallengeTypes, error) {
	// Get challenge
	gcsp := sentry.StartSpan(fe.Context, "authentik.outposts.flow_executor.get_challenge")
	req := fe.api.FlowsApi.FlowsExecutorGet(gcsp.Context(), fe.flowSlug).Query(fe.Params.Encode())
	challenge, _, err := req.Execute()
	if err != nil {
		return nil, err
	}
	i := challenge.GetActualInstance()
	if i == nil {
		return nil, errors.New("response instance was null")
	}
	ch := i.(challengeInt)
	fe.log.WithField("component", ch.GetComponent()).WithField("type", ch.GetType()).Debug("Got challenge")
	gcsp.SetTag("authentik.flow.challenge", string(ch.GetType()))
	gcsp.SetTag("authentik.flow.component", ch.GetComponent())
	gcsp.Finish()
	FlowTimingGet.With(prometheus.Labels{
		"stage": ch.GetComponent(),
		"flow":  fe.flowSlug,
	}).Observe(float64(gcsp.EndTime.Sub(gcsp.StartTime)) / float64(time.Second))
	FlowTimingGetLegacy.With(prometheus.Labels{
		"stage": ch.GetComponent(),
		"flow":  fe.flowSlug,
	}).Observe(float64(gcsp.EndTime.Sub(gcsp.StartTime)))
	return challenge, nil
}

func (fe *FlowExecutor) solveFlowChallenge(challenge *api.ChallengeTypes, depth int) (bool, error) {
	// Resole challenge
	scsp := sentry.StartSpan(fe.Context, "authentik.outposts.flow_executor.solve_challenge")
	responseReq := fe.api.FlowsApi.FlowsExecutorSolve(scsp.Context(), fe.flowSlug).Query(fe.Params.Encode())
	i := challenge.GetActualInstance()
	if i == nil {
		return false, errors.New("response request instance was null")
	}
	ch := i.(challengeInt)

	// Check for any validation errors that we might've gotten
	if len(ch.GetResponseErrors()) > 0 {
		for key, errs := range ch.GetResponseErrors() {
			for _, err := range errs {
				return false, fmt.Errorf("flow error %s: %s", key, err.String)
			}
		}
	}

	switch ch.GetType() {
	case api.CHALLENGECHOICES_REDIRECT:
		return true, nil
	case api.CHALLENGECHOICES_NATIVE:
		if ch.GetComponent() == string(StageAccessDenied) {
			return false, nil
		}
		solver, ok := fe.solvers[StageComponent(ch.GetComponent())]
		if !ok {
			return false, fmt.Errorf("unsupported challenge type %s", ch.GetComponent())
		}
		rr, err := solver(challenge, responseReq)
		if err != nil {
			return false, err
		}
		responseReq = responseReq.FlowChallengeResponseRequest(rr)
	}

	response, _, err := responseReq.Execute()
	if err != nil {
		return false, fmt.Errorf("failed to submit challenge %w", err)
	}
	i = response.GetActualInstance()
	if i == nil {
		return false, errors.New("response instance was null")
	}
	ch = i.(challengeInt)
	fe.log.WithField("component", ch.GetComponent()).WithField("type", ch.GetType()).Debug("Got response")
	scsp.SetTag("authentik.flow.challenge", string(ch.GetType()))
	scsp.SetTag("authentik.flow.component", ch.GetComponent())
	scsp.Finish()
	FlowTimingPost.With(prometheus.Labels{
		"stage": ch.GetComponent(),
		"flow":  fe.flowSlug,
	}).Observe(float64(scsp.EndTime.Sub(scsp.StartTime)) / float64(time.Second))
	FlowTimingPostLegacy.With(prometheus.Labels{
		"stage": ch.GetComponent(),
		"flow":  fe.flowSlug,
	}).Observe(float64(scsp.EndTime.Sub(scsp.StartTime)))

	if depth >= 10 {
		return false, errors.New("exceeded stage recursion depth")
	}
	return fe.solveFlowChallenge(response, depth+1)
}
