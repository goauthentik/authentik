package flow

import (
	"errors"
	"strconv"
	"strings"

	"goauthentik.io/api/v3"
)

func (fe *FlowExecutor) checkPasswordMFA() {
	password := fe.getAnswer(StagePassword)
	// We already have an authenticator answer
	if fe.Answers[StageAuthenticatorValidate] != "" {
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
	// authenticator answer isn't purely numerical, so won't be value
	if _, err := strconv.Atoi(authenticator); err != nil {
		return
	}
	if len(authenticator) != 6 {
		return
	}
	fe.Answers[StagePassword] = password[:idx]
	fe.Answers[StageAuthenticatorValidate] = authenticator
}

func (fe *FlowExecutor) solveChallenge_Identification(challenge *api.ChallengeTypes, req api.ApiFlowsExecutorSolveRequest) (api.FlowChallengeResponseRequest, error) {
	r := api.NewIdentificationChallengeResponseRequest(fe.getAnswer(StageIdentification))
	fe.checkPasswordMFA()
	r.SetPassword(fe.getAnswer(StagePassword))
	return api.IdentificationChallengeResponseRequestAsFlowChallengeResponseRequest(r), nil
}

func (fe *FlowExecutor) solveChallenge_Password(challenge *api.ChallengeTypes, req api.ApiFlowsExecutorSolveRequest) (api.FlowChallengeResponseRequest, error) {
	fe.checkPasswordMFA()
	r := api.NewPasswordChallengeResponseRequest(fe.getAnswer(StagePassword))
	return api.PasswordChallengeResponseRequestAsFlowChallengeResponseRequest(r), nil
}

func (fe *FlowExecutor) solveChallenge_UserLogin(challenge *api.ChallengeTypes, req api.ApiFlowsExecutorSolveRequest) (api.FlowChallengeResponseRequest, error) {
	r := api.NewUserLoginChallengeResponseRequest(true)
	return api.UserLoginChallengeResponseRequestAsFlowChallengeResponseRequest(r), nil
}

func (fe *FlowExecutor) solveChallenge_AuthenticatorValidate(challenge *api.ChallengeTypes, req api.ApiFlowsExecutorSolveRequest) (api.FlowChallengeResponseRequest, error) {
	// We only support duo and code-based authenticators, check if that's allowed
	var deviceChallenge *api.DeviceChallenge
	inner := api.NewAuthenticatorValidationChallengeResponseRequest()
	for _, devCh := range challenge.AuthenticatorValidationChallenge.DeviceChallenges {
		if devCh.DeviceClass == string(api.DEVICECLASSESENUM_DUO) {
			deviceChallenge = &devCh
			devId, err := strconv.ParseInt(deviceChallenge.DeviceUid, 10, 32)
			if err != nil {
				return api.FlowChallengeResponseRequest{}, errors.New("failed to convert duo device id to int")
			}
			devId32 := int32(devId)
			inner.SelectedChallenge = (*api.DeviceChallengeRequest)(deviceChallenge)
			inner.Duo = &devId32
		}
		if devCh.DeviceClass == string(api.DEVICECLASSESENUM_STATIC) ||
			devCh.DeviceClass == string(api.DEVICECLASSESENUM_TOTP) {
			fe.checkPasswordMFA()
			// Only use code-based devices if we have a code in the entered password,
			// and we haven't selected a push device yet
			if deviceChallenge == nil && fe.getAnswer(StageAuthenticatorValidate) != "" {
				deviceChallenge = &devCh
				inner.SelectedChallenge = (*api.DeviceChallengeRequest)(deviceChallenge)
				code := fe.getAnswer(StageAuthenticatorValidate)
				inner.Code = &code
			}
		}
	}
	if deviceChallenge == nil {
		return api.FlowChallengeResponseRequest{}, errors.New("no compatible authenticator class found")
	}
	return api.AuthenticatorValidationChallengeResponseRequestAsFlowChallengeResponseRequest(inner), nil
}
