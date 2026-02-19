use tracing::Level;
use tracing_subscriber::{fmt, EnvFilter};

pub fn init_logging() -> Result<(), Box<dyn std::error::Error>> {
    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new("info,neuroflow=debug"));

    fmt()
        .with_env_filter(filter)
        .with_target(true)
        .with_level(true)
        .with_thread_ids(true)
        .with_file(true)
        .with_line_number(true)
        .init();

    tracing::info!("Logging initialized");
    Ok(())
}

pub fn init_test_logging() {
    let _ = fmt()
        .with_max_level(Level::DEBUG)
        .with_test_writer()
        .try_init();
}