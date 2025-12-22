# flake8: noqa
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """
SELECT "authentik_core_group"."name" AS "name",
       Count("authentik_core_group"."name") AS "name__count"
FROM "authentik_core_group" GROUP  BY 1
HAVING Count("authentik_core_group"."name") > 1
ORDER  BY 2 DESC,
          1 ASC
"""


class DuplicateNameError(RuntimeError):
    pass


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        # migration that introduces the uniqueness
        self.cur.execute(
            "select count(*) from django_migrations where app = 'authentik_core' and name = '0056_user_roles';"
        )
        return not bool(self.cur.rowcount)

    def run(self):
        rows = self.cur.execute(SQL_STATEMENT).fetchall()
        if len(rows):
            for row in rows:
                self.log.error(
                    "Group with duplicate name detected", name=row["name"], count=row["name__count"]
                )
            raise DuplicateNameError(
                f"authentik 2025.12 forbids duplicate group names. For a list of duplicate groups, see logging output above. Please rename the offending groups and re-run the migration. For more information, see: https://version-2025-12.goauthentik.io/releases/2025.12/#group-name-uniqueness"
            )
