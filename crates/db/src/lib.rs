use std::sync::OnceLock;

use eyre::Result;
use sea_orm::DatabaseConnection;
use sqlx::PgPool;

static DB: OnceLock<PgPool> = OnceLock::new();

pub async fn init() -> Result<()> {
    todo!()
}

pub fn get_db() -> DatabaseConnection {
    DatabaseConnection::from(get_raw_db().clone())
}

pub fn get_raw_db() -> &'static PgPool {
    DB.get().unwrap()
}
