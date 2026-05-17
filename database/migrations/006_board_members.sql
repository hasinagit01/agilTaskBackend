CREATE TABLE IF NOT EXISTS board_members (
    board_id   INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK(role IN ('owner', 'member', 'viewer')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (board_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_board_members_user_id ON board_members(user_id);
