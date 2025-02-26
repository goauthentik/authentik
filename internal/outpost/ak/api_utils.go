package ak

import (
	"errors"
	"net/http"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
)

// Generic interface that mimics a generated request by the API client
// Requires mainly `Treq` which will be the actual request type, and
// `Tres` which is the response type
type PaginatorRequest[Treq any, Tres any] interface {
	Page(page int32) Treq
	PageSize(size int32) Treq
	Execute() (Tres, *http.Response, error)
}

// Generic interface that mimics a generated response by the API client
type PaginatorResponse[Tobj any] interface {
	GetResults() []Tobj
	GetPagination() api.Pagination
}

// Paginator options for page size
type PaginatorOptions struct {
	PageSize int
	Logger   *log.Entry
}

// Automatically fetch all objects from an API endpoint using the pagination
// data received from the server.
func Paginator[Tobj any, Treq any, Tres PaginatorResponse[Tobj]](
	req PaginatorRequest[Treq, Tres],
	opts PaginatorOptions,
) ([]Tobj, error) {
	var bfreq, cfreq interface{}
	fetchOffset := func(page int32) (Tres, error) {
		bfreq = req.Page(page)
		cfreq = bfreq.(PaginatorRequest[Treq, Tres]).PageSize(int32(opts.PageSize))
		res, _, err := cfreq.(PaginatorRequest[Treq, Tres]).Execute()
		if err != nil {
			opts.Logger.WithError(err).WithField("page", page).Warning("failed to fetch page")
		}
		return res, err
	}
	var page int32 = 1
	errs := make([]error, 0)
	objects := make([]Tobj, 0)
	for {
		apiObjects, err := fetchOffset(page)
		if err != nil {
			errs = append(errs, err)
			continue
		}
		objects = append(objects, apiObjects.GetResults()...)
		if apiObjects.GetPagination().Next > 0 {
			page += 1
		} else {
			break
		}
	}
	return objects, errors.Join(errs...)
}
