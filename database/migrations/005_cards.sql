CREATE TABLE IF NOT EXISTS cards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    column_id   INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    position    INTEGER NOT NULL DEFAULT 0,
    due_date    TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id);
