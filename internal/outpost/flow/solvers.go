package flow

import (
	"errors"
	"strconv"

	"goauthentik.io/api/v3"
)

func (fe *FlowExecutor) solveChallenge_Identification(challenge *api.ChallengeTypes, req api.ApiFlowsExecutorSolveRequest) (api.FlowChallengeResponseRequest, error) {
	r := api.NewIdentificationChallengeResponseRequest(fe.getAnswer(StageIdentification))
	r.SetPassword(fe.getAnswer(StagePassword))
	return api.IdentificationChallengeResponseRequestAsFlowChallengeResponseRequest(r), nil
}

func (fe *FlowExecutor) solveChallenge_Password(challenge *api.ChallengeTypes, req api.ApiFlowsExecutorSolveRequest) (api.FlowChallengeResponseRequest, error) {
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
