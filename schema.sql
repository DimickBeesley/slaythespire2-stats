-- Slay the Spire 2 Run History Schema
-- Generated from analysis of .run JSON files (schema_version 8)

-- ============================================================
-- RUNS
-- ============================================================

CREATE TABLE runs (
    start_time      BIGINT      PRIMARY KEY,    -- Unix timestamp, natural unique key
    seed            VARCHAR     NOT NULL,
    build_id        VARCHAR     NOT NULL,
    schema_version  INT         NOT NULL,
    game_mode       VARCHAR     NOT NULL,
    ascension       INT         NOT NULL,
    platform_type   VARCHAR     NOT NULL,
    run_time        INT         NOT NULL,   -- seconds
    win             BOOLEAN     NOT NULL,
    was_abandoned   BOOLEAN     NOT NULL,
    is_single_player BOOLEAN    NOT NULL,
    killed_by_encounter VARCHAR NOT NULL,   -- "NONE.NONE" if not killed by encounter
    killed_by_event     VARCHAR NOT NULL    -- "NONE.NONE" if not killed by event
);

-- The three acts selected for the run (e.g. "ACT.OVERGROWTH")
CREATE TABLE run_acts (
    id              BIGSERIAL PRIMARY KEY,
    run_start_time  BIGINT  NOT NULL REFERENCES runs(start_time) ON DELETE CASCADE,
    act_order       INT     NOT NULL,           -- 0-indexed position in acts array
    act_id          VARCHAR NOT NULL
);

-- ============================================================
-- PLAYERS
-- ============================================================

-- One row per player per run (solo runs always have player_num = 1)
CREATE TABLE run_players (
    id                      BIGSERIAL PRIMARY KEY,
    run_start_time          BIGINT  NOT NULL REFERENCES runs(start_time) ON DELETE CASCADE,
    player_num              INT     NOT NULL,   -- 1-based position in players array (1–4)
    steam_id                BIGINT  NOT NULL,   -- JSON "id" field (Steam ID in multiplayer, 1 for solo)
    character               VARCHAR NOT NULL,   -- e.g. "CHARACTER.IRONCLAD"
    max_potion_slot_count   INT     NOT NULL,
    UNIQUE (run_start_time, player_num)
);

-- Final deck state at end of run
CREATE TABLE player_deck_cards (
    id                      BIGSERIAL PRIMARY KEY,
    run_player_id           BIGINT  NOT NULL REFERENCES run_players(id) ON DELETE CASCADE,
    card_id                 VARCHAR NOT NULL,
    floor_added_to_deck     INT,
    current_upgrade_level   INT,
    enchantment_id          VARCHAR,            -- e.g. "ENCHANTMENT.NIMBLE"
    enchantment_amount      INT
);

-- Final relic list at end of run (order preserved)
CREATE TABLE player_relics (
    id              BIGSERIAL PRIMARY KEY,
    run_player_id   BIGINT  NOT NULL REFERENCES run_players(id) ON DELETE CASCADE,
    relic_order     INT     NOT NULL,
    relic_id        VARCHAR NOT NULL,
    floor_obtained  INT
);

-- Potions held at end of run (usually empty)
CREATE TABLE player_potions (
    id            BIGSERIAL PRIMARY KEY,
    run_player_id BIGINT  NOT NULL REFERENCES run_players(id) ON DELETE CASCADE,
    potion_id     VARCHAR NOT NULL
);

-- ============================================================
-- MAP POINT HISTORY
-- ============================================================

-- One row per node visited on the map
-- map_point_history[act_index][point_index]
CREATE TABLE map_points (
    id              BIGSERIAL PRIMARY KEY,
    run_start_time  BIGINT  NOT NULL REFERENCES runs(start_time) ON DELETE CASCADE,
    act_index       INT     NOT NULL,   -- 0-indexed act
    point_index     INT     NOT NULL,   -- 0-indexed position within act
    map_point_type  VARCHAR NOT NULL    -- "monster","elite","boss","rest_site","shop","treasure","unknown","ancient"
);

-- Rooms within each map point (usually 1, can be multiple)
CREATE TABLE rooms (
    id          BIGSERIAL PRIMARY KEY,
    map_point_id BIGINT  NOT NULL REFERENCES map_points(id) ON DELETE CASCADE,
    room_index  INT     NOT NULL,
    model_id    VARCHAR,                -- null for rest_site/shop/treasure
    room_type   VARCHAR NOT NULL,
    turns_taken INT
);

-- Monster IDs present in a room (only combat rooms)
CREATE TABLE room_monsters (
    id          BIGSERIAL PRIMARY KEY,
    room_id     BIGINT  NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    monster_id  VARCHAR NOT NULL
);

-- ============================================================
-- PLAYER STATS (one row per player per map point)
-- ============================================================

CREATE TABLE player_stats (
    id              BIGSERIAL PRIMARY KEY,
    map_point_id    BIGINT  NOT NULL REFERENCES map_points(id) ON DELETE CASCADE,
    run_player_id   BIGINT  NOT NULL REFERENCES run_players(id) ON DELETE CASCADE,
    player_num      INT     NOT NULL,   -- 1-based position, matches run_players.player_num
    steam_id        BIGINT  NOT NULL,   -- JSON "player_id" field
    current_gold    INT     NOT NULL,
    current_hp      INT     NOT NULL,
    max_hp          INT     NOT NULL,
    damage_taken    INT     NOT NULL,
    hp_healed       INT     NOT NULL,
    gold_gained     INT     NOT NULL,
    gold_lost       INT     NOT NULL,
    gold_spent      INT     NOT NULL,
    gold_stolen     INT     NOT NULL,
    max_hp_gained   INT     NOT NULL,
    max_hp_lost     INT     NOT NULL
);

-- ============================================================
-- CHOICES (all reference player_stats)
-- ============================================================

-- Card offered at a combat/event reward
CREATE TABLE card_choices (
    id                      BIGSERIAL PRIMARY KEY,
    player_stats_id         BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    card_id                 VARCHAR NOT NULL,
    floor_added_to_deck     INT,
    current_upgrade_level   INT,
    was_picked              BOOLEAN NOT NULL
);

-- Relic offered at treasures, elites, shops, ancient
CREATE TABLE relic_choices (
    id              BIGSERIAL PRIMARY KEY,
    player_stats_id BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    relic_id        VARCHAR NOT NULL,
    was_picked      BOOLEAN NOT NULL
);

-- Potion offered after combat or at events
CREATE TABLE potion_choices (
    id              BIGSERIAL PRIMARY KEY,
    player_stats_id BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    potion_id       VARCHAR NOT NULL,
    was_picked      BOOLEAN NOT NULL
);

-- Neow's blessing options at start of each act
CREATE TABLE ancient_choices (
    id              BIGSERIAL PRIMARY KEY,
    player_stats_id BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    text_key        VARCHAR NOT NULL,   -- e.g. "PRECISE_SCISSORS"
    title_key       VARCHAR NOT NULL,   -- e.g. "PRECISE_SCISSORS.title"
    title_table     VARCHAR NOT NULL,   -- e.g. "relics"
    was_chosen      BOOLEAN NOT NULL
);

-- Options chosen at events (may have associated variables)
CREATE TABLE event_choices (
    id              BIGSERIAL PRIMARY KEY,
    player_stats_id BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    choice_order    INT     NOT NULL,
    title_key       VARCHAR NOT NULL,
    title_table     VARCHAR NOT NULL
);

-- Dynamic string variables attached to an event choice
CREATE TABLE event_choice_variables (
    id                BIGSERIAL PRIMARY KEY,
    event_choice_id   BIGINT  NOT NULL REFERENCES event_choices(id) ON DELETE CASCADE,
    var_name          VARCHAR NOT NULL,
    var_type          VARCHAR,
    decimal_value     NUMERIC,
    bool_value        BOOLEAN,
    string_value      VARCHAR
);

-- Rest site actions taken (e.g. "HEAL", "SMITH", "DIG")
CREATE TABLE rest_site_choices (
    id              BIGSERIAL PRIMARY KEY,
    player_stats_id BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    choice_order    INT     NOT NULL,
    choice          VARCHAR NOT NULL
);

-- ============================================================
-- CARD / POTION EVENTS (all reference player_stats)
-- ============================================================

-- Cards added to deck at this node
CREATE TABLE stat_cards_gained (
    id                      BIGSERIAL PRIMARY KEY,
    player_stats_id         BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    card_id                 VARCHAR NOT NULL,
    floor_added_to_deck     INT,
    current_upgrade_level   INT,
    enchantment_id          VARCHAR,
    enchantment_amount      INT
);

-- Cards removed from deck at this node (shop purge, event)
CREATE TABLE stat_cards_removed (
    id                  BIGSERIAL PRIMARY KEY,
    player_stats_id     BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    card_id             VARCHAR NOT NULL,
    floor_added_to_deck INT
);

-- Cards transformed at this node (Neow or event)
CREATE TABLE stat_cards_transformed (
    id                          BIGSERIAL PRIMARY KEY,
    player_stats_id             BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    original_card_id            VARCHAR NOT NULL,
    original_floor_added_to_deck INT,
    final_card_id               VARCHAR NOT NULL,
    final_floor_added_to_deck   INT
);

-- Cards that received an enchantment at this node
CREATE TABLE stat_cards_enchanted (
    id                      BIGSERIAL PRIMARY KEY,
    player_stats_id         BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    card_id                 VARCHAR NOT NULL,
    floor_added_to_deck     INT,
    current_upgrade_level   INT,
    enchantment_id          VARCHAR NOT NULL,
    enchantment_amount      INT
);

-- Cards upgraded at a rest site (SMITH)
CREATE TABLE stat_cards_upgraded (
    id              BIGSERIAL PRIMARY KEY,
    player_stats_id BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    card_id         VARCHAR NOT NULL
);

-- Potions consumed during combat at this node
CREATE TABLE stat_potions_used (
    id              BIGSERIAL PRIMARY KEY,
    player_stats_id BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    potion_id       VARCHAR NOT NULL
);

-- Potions discarded (e.g. via events)
CREATE TABLE stat_potions_discarded (
    id              BIGSERIAL PRIMARY KEY,
    player_stats_id BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    potion_id       VARCHAR NOT NULL
);

-- Colorless cards bought at shops
CREATE TABLE stat_bought_colorless (
    id              BIGSERIAL PRIMARY KEY,
    player_stats_id BIGINT  NOT NULL REFERENCES player_stats(id) ON DELETE CASCADE,
    card_id         VARCHAR NOT NULL
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX ON run_acts (run_start_time);
CREATE INDEX ON run_players (run_start_time);
CREATE INDEX ON player_deck_cards (run_player_id);
CREATE INDEX ON player_relics (run_player_id);
CREATE INDEX ON map_points (run_start_time);
CREATE INDEX ON rooms (map_point_id);
CREATE INDEX ON player_stats (map_point_id);
CREATE INDEX ON player_stats (run_player_id);
CREATE INDEX ON card_choices (player_stats_id);
CREATE INDEX ON relic_choices (player_stats_id);
CREATE INDEX ON potion_choices (player_stats_id);
CREATE INDEX ON ancient_choices (player_stats_id);
CREATE INDEX ON event_choices (player_stats_id);
CREATE INDEX ON rest_site_choices (player_stats_id);
CREATE INDEX ON stat_cards_gained (player_stats_id);
CREATE INDEX ON stat_cards_removed (player_stats_id);
CREATE INDEX ON stat_cards_transformed (player_stats_id);
CREATE INDEX ON stat_cards_enchanted (player_stats_id);
CREATE INDEX ON stat_cards_upgraded (player_stats_id);
CREATE INDEX ON stat_potions_used (player_stats_id);
CREATE INDEX ON stat_potions_discarded (player_stats_id);
CREATE INDEX ON stat_bought_colorless (player_stats_id);
