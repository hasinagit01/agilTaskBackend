CREATE TABLE IF NOT EXISTS card_labels (
    card_id  INTEGER NOT NULL REFERENCES cards(id)  ON DELETE CASCADE,
    label_id INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    PRIMARY KEY (card_id, label_id)
);
