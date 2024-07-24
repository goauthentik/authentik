package ak

import (
	"errors"
	"net/http"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
)

type PaginatorRequest[Tobj any, Treq any, Tres any] interface {
	Page(page int32) Treq
	PageSize(size int32) Treq
	Execute() (Tres, *http.Response, error)
}

type PaginatorResponse[Tobj any] interface {
	GetResults() []Tobj
	GetPagination() api.Pagination
}

type PaginatorOptions struct {
	PageSize int
	Logger   *log.Entry
}

func Paginator[Tobj any, Treq any, Tres PaginatorResponse[Tobj]](
	req PaginatorRequest[Tobj, Treq, Tres],
	opts PaginatorOptions,
) ([]Tobj, error) {
	fetchOffset := func(page int32) (Tres, error) {
		req.Page(page)
		req.PageSize(int32(opts.PageSize))
		res, _, err := req.Execute()
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
