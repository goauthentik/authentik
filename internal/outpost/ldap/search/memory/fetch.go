package memory

import (
	"context"

	"goauthentik.io/api/v3"
)

const pageSize = 100

func (ms *MemorySearcher) FetchUsers() []api.User {
	fetchUsersOffset := func(page int) (*api.PaginatedUserList, error) {
		users, _, err := ms.si.GetAPIClient().CoreApi.CoreUsersList(context.TODO()).Page(int32(page)).PageSize(pageSize).Execute()
		if err != nil {
			ms.log.WithError(err).Warning("failed to update users")
			return nil, err
		}
		ms.log.WithField("page", page).WithField("count", len(users.Results)).Debug("fetched users")
		return users, nil
	}
	page := 1
	users := make([]api.User, 0)
	for {
		apiUsers, err := fetchUsersOffset(page)
		if err != nil {
			return users
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

func (ms *MemorySearcher) FetchGroups() []api.Group {
	fetchGroupsOffset := func(page int) (*api.PaginatedGroupList, error) {
		groups, _, err := ms.si.GetAPIClient().CoreApi.CoreGroupsList(context.TODO()).Page(int32(page)).PageSize(pageSize).Execute()
		if err != nil {
			ms.log.WithError(err).Warning("failed to update groups")
			return nil, err
		}
		ms.log.WithField("page", page).WithField("count", len(groups.Results)).Debug("fetched groups")
		return groups, nil
	}
	page := 1
	groups := make([]api.Group, 0)
	for {
		apiGroups, err := fetchGroupsOffset(page)
		if err != nil {
			return groups
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
