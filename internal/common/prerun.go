package common

import (
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

func PreRun(cmd *cobra.Command, args []string) {
	log.SetLevel(log.DebugLevel)
	log.SetFormatter(&log.JSONFormatter{
		FieldMap: log.FieldMap{
			log.FieldKeyMsg:  "event",
			log.FieldKeyTime: "timestamp",
		},
		DisableHTMLEscape: true,
	})
}
