package ak

import (
	"errors"
	"net/http"
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
)

type fakeAPIType struct{}

type fakeAPIResponse struct {
	results    []fakeAPIType
	pagination api.Pagination
}

func (fapi *fakeAPIResponse) GetResults() []fakeAPIType     { return fapi.results }
func (fapi *fakeAPIResponse) GetPagination() api.Pagination { return fapi.pagination }

type fakeAPIRequest struct {
	res  *fakeAPIResponse
	http *http.Response
	err  error
}

func (fapi *fakeAPIRequest) Page(page int32) *fakeAPIRequest     { return fapi }
func (fapi *fakeAPIRequest) PageSize(size int32) *fakeAPIRequest { return fapi }
func (fapi *fakeAPIRequest) Execute() (*fakeAPIResponse, *http.Response, error) {
	return fapi.res, fapi.http, fapi.err
}

func Test_Simple(t *testing.T) {
	req := &fakeAPIRequest{
		res: &fakeAPIResponse{
			results: []fakeAPIType{
				{},
			},
			pagination: api.Pagination{
				TotalPages: 1,
			},
		},
	}
	res, err := Paginator(req, PaginatorOptions{})
	assert.NoError(t, err)
	assert.Len(t, res, 1)
}

func Test_BadRequest(t *testing.T) {
	req := &fakeAPIRequest{
		http: &http.Response{
			StatusCode: 400,
		},
		err: errors.New("foo"),
	}
	res, err := Paginator(req, PaginatorOptions{})
	assert.Error(t, err)
	assert.Equal(t, []fakeAPIType{}, res)
}

// func Test_PaginatorCompile(t *testing.T) {
// 	req := api.ApiCoreUsersListRequest{}
// 	Paginator(req, PaginatorOptions{
// 		PageSize: 100,
// 	})
// }

// func Test_PaginatorCompileExplicit(t *testing.T) {
// 	req := api.ApiCoreUsersListRequest{}
// 	Paginator[
// 		api.User,
// 		api.ApiCoreUsersListRequest,
// 		*api.PaginatedUserList,
// 	](req, PaginatorOptions{
// 		PageSize: 100,
// 	})
// }

// func Test_PaginatorCompileOther(t *testing.T) {
// 	req := api.ApiOutpostsProxyListRequest{}
// 	Paginator(req, PaginatorOptions{
// 		PageSize: 100,
// 	})
// }
