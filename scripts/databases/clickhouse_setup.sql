-- ClickHouse table for storing document chunks
CREATE TABLE IF NOT EXISTS documents (
    id UInt64,
    content String,
    created DateTime DEFAULT now()
) ENGINE = MergeTree() ORDER BY id;
