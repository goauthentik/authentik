-- Create replication role if it doesn't exist
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'replica') THEN
        CREATE ROLE replica WITH REPLICATION LOGIN PASSWORD '${POSTGRES_PASSWORD}';
    END IF;
END $$;

-- Create replication slot if it doesn't exist
SELECT pg_create_physical_replication_slot('replica_slot', true);
