package ak

type Outpost interface {
	Start() error
	Refresh() error
}
