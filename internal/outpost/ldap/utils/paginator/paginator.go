package paginator

import (
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
)

const PageSize = 100

func FetchUsers(req api.ApiCoreUsersListRequest) []api.User {
	fetchUsersOffset := func(page int) (*api.PaginatedUserList, error) {
		users, _, err := req.Page(int32(page)).PageSize(PageSize).Execute()
		if err != nil {
			log.WithError(err).Warning("failed to update users")
			return nil, err
		}
		log.WithField("page", page).WithField("count", len(users.Results)).Debug("fetched users")
		return users, nil
	}
	page := 1
	users := make([]api.User, 0)
	for {
		apiUsers, err := fetchUsersOffset(page)
		if err != nil {
			log.WithError(err).WithField("page", page).Warn("Failed to fetch user page")
			continue
		}
		users = append(users, apiUsers.Results...)
		if apiUsers.Pagination.Next > 0 {
			page += 1
		} else {
			break
		}
	}
	return users
}

func FetchGroups(req api.ApiCoreGroupsListRequest) []api.Group {
	fetchGroupsOffset := func(page int) (*api.PaginatedGroupList, error) {
		groups, _, err := req.Page(int32(page)).PageSize(PageSize).Execute()
		if err != nil {
			log.WithError(err).Warning("failed to update groups")
			return nil, err
		}
		log.WithField("page", page).WithField("count", len(groups.Results)).Debug("fetched groups")
		return groups, nil
	}
	page := 1
	groups := make([]api.Group, 0)
	for {
		apiGroups, err := fetchGroupsOffset(page)
		if err != nil {
			log.WithError(err).WithField("page", page).Warn("Failed to fetch group page")
			continue
		}
		groups = append(groups, apiGroups.Results...)
		if apiGroups.Pagination.Next > 0 {
			page += 1
		} else {
			break
		}
	}
	return groups
}
