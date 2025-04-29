package main

import (
	"context"
	"crypto/tls"
	"encoding/base64"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"time"

	"github.com/mitchellh/mapstructure"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"

	"goauthentik.io/internal/common"
	"goauthentik.io/internal/debug"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/ak/healthcheck"
)

const helpMessage = `authentik SCIM

Required environment variables:
- AUTHENTIK_HOST: URL to connect to (format "http://authentik.company")
- AUTHENTIK_TOKEN: Token to authenticate with
- AUTHENTIK_INSECURE: Skip SSL Certificate verification`

var rootCmd = &cobra.Command{
	Long: helpMessage,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		log.SetLevel(log.DebugLevel)
		log.SetFormatter(&log.JSONFormatter{
			FieldMap: log.FieldMap{
				log.FieldKeyMsg:  "event",
				log.FieldKeyTime: "timestamp",
			},
			DisableHTMLEscape: true,
		})
	},
	Run: func(cmd *cobra.Command, args []string) {
		debug.EnableDebugServer()
		akURL, found := os.LookupEnv("AUTHENTIK_HOST")
		if !found {
			fmt.Println("env AUTHENTIK_HOST not set!")
			fmt.Println(helpMessage)
			os.Exit(1)
		}
		akToken, found := os.LookupEnv("AUTHENTIK_TOKEN")
		if !found {
			fmt.Println("env AUTHENTIK_TOKEN not set!")
			fmt.Println(helpMessage)
			os.Exit(1)
		}

		akURLActual, err := url.Parse(akURL)
		if err != nil {
			fmt.Println(err)
			fmt.Println(helpMessage)
			os.Exit(1)
		}

		ex := common.Init()
		defer common.Defer()
		go func() {
			for {
				<-ex
				os.Exit(0)
			}
		}()

		ac := ak.NewAPIController(*akURLActual, akToken)
		if ac == nil {
			os.Exit(1)
		}
		defer ac.Shutdown()

		ac.Server = &SCIMOutpost{
			ac:  ac,
			log: log.WithField("logger", "authentik.outpost.scim"),
		}

		err = ac.Start()
		if err != nil {
			log.WithError(err).Panic("Failed to run server")
		}

		for {
			<-ex
		}
	},
}

type HTTPRequest struct {
	Uid       string              `mapstructure:"uid"`
	Method    string              `mapstructure:"method"`
	URL       string              `mapstructure:"url"`
	Headers   map[string][]string `mapstructure:"headers"`
	Body      interface{}         `mapstructure:"body"`
	SSLVerify bool                `mapstructure:"ssl_verify"`
	Timeout   int                 `mapstructure:"timeout"`
}

type RequestArgs struct {
	Request         HTTPRequest `mapstructure:"request"`
	ResponseChannel string      `mapstructure:"response_channel"`
}

type SCIMOutpost struct {
	ac  *ak.APIController
	log *log.Entry
}

func (s *SCIMOutpost) Type() string                         { return "SCIM" }
func (s *SCIMOutpost) Stop() error                          { return nil }
func (s *SCIMOutpost) Refresh() error                       { return nil }
func (s *SCIMOutpost) TimerFlowCacheExpiry(context.Context) {}

func (s *SCIMOutpost) Start() error {
	s.ac.AddWSHandler(func(ctx context.Context, args map[string]interface{}) {
		rd := RequestArgs{}
		err := mapstructure.Decode(args, &rd)
		if err != nil {
			s.log.WithError(err).Warning("failed to parse http request")
			return
		}
		s.log.WithField("rd", rd).WithField("raw", args).Debug("request data")
		ctx, canc := context.WithTimeout(ctx, time.Duration(rd.Request.Timeout)*time.Second)
		defer canc()

		req, err := http.NewRequestWithContext(ctx, rd.Request.Method, rd.Request.URL, nil)
		if err != nil {
			s.log.WithError(err).Warning("failed to create request")
			return
		}

		tr := &http.Transport{
			TLSClientConfig:       &tls.Config{InsecureSkipVerify: !rd.Request.SSLVerify},
			TLSHandshakeTimeout:   time.Duration(rd.Request.Timeout) * time.Second,
			IdleConnTimeout:       time.Duration(rd.Request.Timeout) * time.Second,
			ResponseHeaderTimeout: time.Duration(rd.Request.Timeout) * time.Second,
			ExpectContinueTimeout: time.Duration(rd.Request.Timeout) * time.Second,
		}
		c := &http.Client{
			Transport: tr,
		}
		s.log.WithField("url", req.URL.Host).Debug("sending HTTP request")
		res, err := c.Do(req)
		if err != nil {
			s.log.WithError(err).Warning("failed to send request")
			return
		}
		body, err := io.ReadAll(res.Body)
		if err != nil {
			s.log.WithError(err).Warning("failed to read body")
			return
		}
		s.log.WithField("res", res.StatusCode).Debug("sending HTTP response")
		err = s.ac.SendWS(ak.WebsocketInstructionProviderSpecific, map[string]interface{}{
			"sub_type":         "http_response",
			"response_channel": rd.ResponseChannel,
			"response": map[string]interface{}{
				"status":    res.StatusCode,
				"final_url": res.Request.URL.String(),
				"headers":   res.Header,
				"body":      base64.StdEncoding.EncodeToString(body),
			},
		})
		if err != nil {
			s.log.WithError(err).Warning("failed to send http response")
			return
		}
	})
	return nil
}

func main() {
	rootCmd.AddCommand(healthcheck.Command)
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}
