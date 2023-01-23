package ak

import (
	"context"
	"time"
)

func (a *APIController) startPeriodicalTasks() {
	ctx, canc := context.WithCancel(context.Background())
	defer canc()
	go a.Server.TimerFlowCacheExpiry(ctx)
	for range time.Tick(time.Duration(a.GlobalConfig.CacheTimeoutFlows) * time.Second) {
		a.logger.WithField("timer", "cache-timeout").Debug("Running periodical tasks")
		a.Server.TimerFlowCacheExpiry(ctx)
	}
}
