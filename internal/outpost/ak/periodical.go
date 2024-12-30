package ak

import (
	"context"
	"time"

	"go.uber.org/zap"
)

func (a *APIController) startPeriodicalTasks() {
	ctx, canc := context.WithCancel(context.Background())
	defer canc()
	go a.Server.TimerFlowCacheExpiry(ctx)
	for range time.Tick(time.Duration(a.GlobalConfig.CacheTimeoutFlows) * time.Second) {
		a.logger.Debug("Running periodical tasks", zap.String("timer", "cache-timeout"))
		a.Server.TimerFlowCacheExpiry(ctx)
	}
}
