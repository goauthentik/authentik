package entrypoint

import (
	"errors"
	"net/url"
	"os"

	"goauthentik.io/internal/common"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/debug"
	"goauthentik.io/internal/outpost/ak"
)

func OutpostMain(appName string, server func(ac *ak.APIController) ak.Outpost) error {
	debug.EnableDebugServer(appName)
	akURL := config.Get().AuthentikHost
	if akURL == "" {
		return errors.New("environment variable `AUTHENTIK_HOST` not set")
	}
	akToken := config.Get().AuthentikToken
	if akToken == "" {
		return errors.New("environment variable `AUTHENTIK_TOKEN` not set")
	}

	akURLActual, err := url.Parse(akURL)
	if err != nil {
		return err
	}

	ex := common.Init()
	defer common.Defer()

	ac := ak.NewAPIController(*akURLActual, akToken)
	if ac == nil {
		os.Exit(1)
	}
	defer ac.Shutdown()

	ac.Server = server(ac)

	err = ac.Start()
	if err != nil {
		ac.Log().WithError(err).Panic("Failed to run server")
		return err
	}

	for {
		<-ex
		return nil
	}
}
