package ak

import (
	"time"
)

func (a *APIController) startPeriodicalTasks() {
	go a.Server.TimerFlowCacheExpiry()
	go func() {
		for range time.Tick(time.Duration(a.GlobalConfig.CacheTimeoutFlows) * time.Second) {
			a.logger.WithField("timer", "cache-timeout").Debug("Running periodical tasks")
			a.Server.TimerFlowCacheExpiry()
		}
	}()
}
