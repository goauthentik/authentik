"""Keep both ACS representations usable while old and new instances share the database."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_providers_saml", "0025_samlprovider__acs_urls"),
    ]

    operations = [
        migrations.AlterField(
            model_name="samlprovider",
            name="_acs_urls",
            field=models.JSONField(
                default=list,
                db_default=[],
                help_text=(
                    "Assertion Consumer Service URLs the provider may send responses to. The "
                    "default entry is used for IdP-initiated logins and requests without an ACS "
                    "URL."
                ),
                verbose_name="ACS URLs",
            ),
        ),
        # Old instances omit `_acs_urls` on INSERT and only write `acs_url` on UPDATE.
        # Synchronize in the database so reads, API serialization, and filters all see the
        # same URLs, even before a new instance has saved the provider.
        # Remove this trigger and function when the deprecated column is removed.
        migrations.RunSQL(
            sql="""
                CREATE FUNCTION authentik_saml_sync_acs_urls() RETURNS trigger
                LANGUAGE plpgsql AS $$
                DECLARE
                    default_index text;
                    default_url text;
                    legacy_write boolean;
                BEGIN
                    SELECT (ordinality - 1)::text, entry->>'url'
                    INTO default_index, default_url
                    FROM jsonb_array_elements(NEW._acs_urls)
                        WITH ORDINALITY AS urls(entry, ordinality)
                    WHERE COALESCE(entry->>'matching_mode', 'strict') = 'strict'
                    ORDER BY COALESCE(entry->>'is_default' = 'true', false) DESC, ordinality
                    LIMIT 1;

                    IF TG_OP = 'INSERT' THEN
                        legacy_write := NEW._acs_urls = '[]'::jsonb;
                    ELSE
                        legacy_write := NEW._acs_urls IS NOT DISTINCT FROM OLD._acs_urls;
                    END IF;

                    IF legacy_write THEN
                        IF default_index IS NOT NULL THEN
                            NEW._acs_urls := jsonb_set(
                                NEW._acs_urls, ARRAY[default_index, 'url'], to_jsonb(NEW.acs_url)
                            );
                        ELSIF NEW.acs_url <> '' THEN
                            NEW._acs_urls := jsonb_build_array(jsonb_build_object(
                                'url', NEW.acs_url, 'matching_mode', 'strict',
                                'index', NULL, 'is_default', true
                            )) || NEW._acs_urls;
                        END IF;
                    ELSE
                        NEW.acs_url := COALESCE(default_url, '');
                    END IF;
                    RETURN NEW;
                END;
                $$;

                CREATE TRIGGER authentik_saml_sync_acs_urls
                BEFORE INSERT OR UPDATE ON authentik_providers_saml_samlprovider
                FOR EACH ROW EXECUTE FUNCTION authentik_saml_sync_acs_urls();

                -- Reconcile any legacy writes made between migrations 0025 and 0026.
                UPDATE authentik_providers_saml_samlprovider SET acs_url = acs_url;
            """,
            reverse_sql="""
                DROP TRIGGER authentik_saml_sync_acs_urls
                    ON authentik_providers_saml_samlprovider;
                DROP FUNCTION authentik_saml_sync_acs_urls();
            """,
        ),
    ]
