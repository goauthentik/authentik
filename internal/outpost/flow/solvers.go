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

func (fe *FlowExecutor) solveChallenge_AuthenticatorValidate(challenge *api.ChallengeTypes, req api.ApiFlowsExecutorSolveRequest) (api.FlowChallengeResponseRequest, error) {
	// We only support duo as authenticator, check if that's allowed
	var deviceChallenge *api.DeviceChallenge
	for _, devCh := range challenge.AuthenticatorValidationChallenge.DeviceChallenges {
		if devCh.DeviceClass == string(api.DEVICECLASSESENUM_DUO) {
			deviceChallenge = &devCh
		}
	}
	if deviceChallenge == nil {
		return api.FlowChallengeResponseRequest{}, errors.New("no compatible authenticator class found")
	}
	devId, err := strconv.Atoi(deviceChallenge.DeviceUid)
	if err != nil {
		return api.FlowChallengeResponseRequest{}, errors.New("failed to convert duo device id to int")
	}
	devId32 := int32(devId)
	inner := api.NewAuthenticatorValidationChallengeResponseRequest()
	inner.SelectedChallenge = (*api.DeviceChallengeRequest)(deviceChallenge)
	inner.Duo = &devId32
	return api.AuthenticatorValidationChallengeResponseRequestAsFlowChallengeResponseRequest(inner), nil
}
