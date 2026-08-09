package ak

import "context"

type Outpost interface {
	Start() error
	Stop() error
	Refresh() error
	TimerFlowCacheExpiry(context.Context)
	Type() string
}
