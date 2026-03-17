from pathlib import Path

import json
import os

import psycopg2

# Load .env from project root if present (without requiring `source`)
_env_file = Path(__file__).parent / '.env'
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#'):
            if _line.startswith('export '):
                _line = _line[7:]
            _key, _, _val = _line.partition('=')
            os.environ.setdefault(_key.strip(), _val.strip())

STS2_STEAM_ROOT = Path.home() / ".local/share/SlayTheSpire2/steam"


def parse_run(run_data):
    return {
        'acts': run_data['acts'],
        'ascension': run_data['ascension'],
        'build_id': run_data['build_id'],
        'game_mode': run_data['game_mode'],
        'is_single_player': len(run_data['players']) == 1,
        'killed_by_encounter': run_data['killed_by_encounter'],
        'killed_by_event': run_data['killed_by_event'],
        'map_point_history': run_data['map_point_history'],
        'platform_type': run_data['platform_type'],
        'players': run_data['players'],
        'run_time': run_data['run_time'],
        'schema_version': run_data['schema_version'],
        'seed': run_data['seed'],
        'start_time': run_data['start_time'],
        'was_abandoned': run_data['was_abandoned'],
        'win': run_data['win']
    }

def handle_map_point_history(mph):
    return mph

def handle_players(player):
    return {
        'character': player['character'],
        'deck': player['deck'],
        'id': player['id'],
        'max_potion_slot_count': player['max_potion_slot_count'],
        'potions': player['potions'],
        'relics': player['relics']
    }

def print_run(run):
    print(f"=== Run Summary ===")
    print(f"  Build:      {run['build_id']}  |  Schema: {run['schema_version']}")
    print(f"  Mode:       {run['game_mode']}  |  Ascension: {run['ascension']}")
    print(f"  Seed:       {run['seed']}")
    print(f"  Result:     {'WIN' if run['win'] else 'LOSS'}  |  Abandoned: {run['was_abandoned']}")
    print(f"  Killed by:  {run['killed_by_encounter']}  /  {run['killed_by_event']}")
    print(f"  Acts:       {', '.join(run['acts'])}")
    print(f"  Run time:   {run['run_time']}s  |  Started: {run['start_time']}")

    print(f"\n=== Players ===")
    for player in run['players']:
        print(f"  Player {player['id']}: {player['character']}")
        print(f"    Potion slots: {player['max_potion_slot_count']}")
        print(f"    Relics:  {', '.join(r['id'] for r in player['relics'])}")
        print(f"    Potions: {', '.join(p['id'] for p in player['potions']) or 'none'}")
        print(f"    Deck ({len(player['deck'])} cards):")
        for card in player['deck']:
            floor_str = f" (floor {card['floor_added_to_deck']})" if 'floor_added_to_deck' in card else ""
            print(f"      - {card['id']}{floor_str}")

    print(f"\n=== Map Point History ===")
    for act_i, act in enumerate(run['map_point_history']):
        print(f"  -- Act {act_i + 1} --")
        for point in act:
            print(f"    [{point['map_point_type']}]")
            for room in point['rooms']:
                monster_ids = room.get('monster_ids')
                monsters = ', '.join(monster_ids) if monster_ids else 'none'
                turns = room.get('turns_taken', '-')
                model = room.get('model_id', '-')
                print(f"      Room: {model}  ({room['room_type']}, {turns} turns, monsters: {monsters})")
            for stats in point['player_stats']:
                print(f"      Player {stats['player_id']} stats:")
                print(f"        HP: {stats['current_hp']}/{stats['max_hp']}  (dmg: {stats['damage_taken']}, healed: {stats['hp_healed']})")
                print(f"        Gold: {stats['current_gold']}  (gained: {stats['gold_gained']}, spent: {stats['gold_spent']}, lost: {stats['gold_lost']}, stolen: {stats['gold_stolen']})")
                if stats.get('cards_gained'):
                    print(f"        Cards gained: {', '.join(c['id'] for c in stats['cards_gained'])}")
                if stats.get('cards_removed'):
                    print(f"        Cards removed: {', '.join(c['id'] for c in stats['cards_removed'])}")
                if stats.get('cards_transformed'):
                    print(f"        Cards transformed: {', '.join(c['original_card']['id'] + ' -> ' + c['final_card']['id'] for c in stats['cards_transformed'])}")
                if stats.get('cards_enchanted'):
                    print(f"        Cards enchanted: {', '.join(c['card']['id'] + ' (' + c['enchantment'] + ')' for c in stats['cards_enchanted'])}")
                if stats.get('upgraded_cards'):
                    print(f"        Cards upgraded: {', '.join(stats['upgraded_cards'])}")
                if stats.get('card_choices'):
                    picked = next((c['card']['id'] for c in stats['card_choices'] if c['was_picked']), 'none')
                    skipped = [c['card']['id'] for c in stats['card_choices'] if not c['was_picked']]
                    print(f"        Card choice: picked {picked}, skipped {', '.join(skipped)}")
                if stats.get('relic_choices'):
                    picked = next((c['choice'] for c in stats['relic_choices'] if c['was_picked']), 'none')
                    print(f"        Relic choice: picked {picked}")
                if stats.get('potion_choices'):
                    picked = next((c['choice'] for c in stats['potion_choices'] if c['was_picked']), 'none')
                    print(f"        Potion choice: picked {picked}")
                if stats.get('potion_used'):
                    print(f"        Potion used: {stats['potion_used']}")
                if stats.get('event_choices'):
                    titles = [c['title']['key'] for c in stats['event_choices']]
                    print(f"        Event choices: {', '.join(titles)}")
                if stats.get('rest_site_choices'):
                    print(f"        Rest site: {', '.join(stats['rest_site_choices'])}")
                if stats.get('ancient_choice'):
                    picked = next((c['TextKey'] for c in stats['ancient_choice'] if c['was_chosen']), 'none')
                    print(f"        Ancient choice: {picked}")


def connect_db():
    # Required: STS2_DB_PASSWORD
    # Optional: STS2_DB_HOST (default: span), STS2_DB_PORT (default: 5432),
    #           STS2_DB_NAME (default: slaythespire2), STS2_DB_USER (default: sts2)
    return psycopg2.connect(
        host=os.environ.get('STS2_DB_HOST', 'span'),
        port=int(os.environ.get('STS2_DB_PORT', 5432)),
        dbname=os.environ.get('STS2_DB_NAME', 'slaythespire2'),
        user=os.environ.get('STS2_DB_USER', 'sts2'),
        password=os.environ['STS2_DB_PASSWORD'],
    )


def run_exists(conn, run):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM runs WHERE start_time = %s", (run['start_time'],))
        return cur.fetchone() is not None


def insert_run(conn, run, path_steam_id):
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO runs (
                    start_time, seed, build_id, schema_version, game_mode,
                    ascension, platform_type, run_time, win, was_abandoned,
                    is_single_player, killed_by_encounter, killed_by_event
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (start_time) DO NOTHING
            """, (
                run['start_time'], run['seed'], run['build_id'], run['schema_version'],
                run['game_mode'], run['ascension'], run['platform_type'], run['run_time'],
                run['win'], run['was_abandoned'], run['is_single_player'],
                run['killed_by_encounter'], run['killed_by_event'],
            ))

            for i, act in enumerate(run['acts']):
                cur.execute(
                    "INSERT INTO run_acts (run_start_time, act_order, act_id) VALUES (%s, %s, %s)",
                    (run['start_time'], i, act),
                )

            player_db_ids = {}   # steam_id -> run_player DB id
            player_nums = {}     # steam_id -> position (1-based)
            for i, player in enumerate(run['players']):
                # Solo runs use 1 as a placeholder; substitute the real Steam ID from the path
                steam_id = path_steam_id if player['id'] == 1 else player['id']
                cur.execute("""
                    INSERT INTO run_players (run_start_time, player_num, steam_id, character, max_potion_slot_count)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (run['start_time'], i + 1, steam_id, player['character'], player['max_potion_slot_count']))
                run_player_id = cur.fetchone()[0]
                player_db_ids[player['id']] = run_player_id
                player_nums[player['id']] = i + 1

                for card in player['deck']:
                    enc = card.get('enchantment') or {}
                    cur.execute("""
                        INSERT INTO player_deck_cards (
                            run_player_id, card_id, floor_added_to_deck,
                            current_upgrade_level, enchantment_id, enchantment_amount
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        run_player_id, card['id'], card.get('floor_added_to_deck'),
                        card.get('current_upgrade_level'), enc.get('id'), enc.get('amount'),
                    ))

                for i, relic in enumerate(player['relics']):
                    cur.execute("""
                        INSERT INTO player_relics (run_player_id, relic_order, relic_id, floor_obtained)
                        VALUES (%s, %s, %s, %s)
                    """, (run_player_id, i, relic['id'], relic.get('floor_added_to_deck')))

                for potion in player['potions']:
                    cur.execute(
                        "INSERT INTO player_potions (run_player_id, potion_id) VALUES (%s, %s)",
                        (run_player_id, potion['id']),
                    )

            for act_i, act in enumerate(run['map_point_history']):
                for point_i, point in enumerate(act):
                    cur.execute("""
                        INSERT INTO map_points (run_start_time, act_index, point_index, map_point_type)
                        VALUES (%s, %s, %s, %s) RETURNING id
                    """, (run['start_time'], act_i, point_i, point['map_point_type']))
                    map_point_id = cur.fetchone()[0]

                    for room_i, room in enumerate(point['rooms']):
                        cur.execute("""
                            INSERT INTO rooms (map_point_id, room_index, model_id, room_type, turns_taken)
                            VALUES (%s, %s, %s, %s, %s) RETURNING id
                        """, (map_point_id, room_i, room.get('model_id'), room['room_type'], room.get('turns_taken')))
                        room_id = cur.fetchone()[0]

                        for monster_id in room.get('monster_ids', []):
                            cur.execute(
                                "INSERT INTO room_monsters (room_id, monster_id) VALUES (%s, %s)",
                                (room_id, monster_id),
                            )

                    for stats in point['player_stats']:
                        stat_steam_id = path_steam_id if stats['player_id'] == 1 else stats['player_id']
                        cur.execute("""
                            INSERT INTO player_stats (
                                map_point_id, run_player_id, player_num, steam_id,
                                current_gold, current_hp, max_hp,
                                damage_taken, hp_healed,
                                gold_gained, gold_lost, gold_spent, gold_stolen,
                                max_hp_gained, max_hp_lost
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                        """, (
                            map_point_id, player_db_ids[stats['player_id']],
                            player_nums[stats['player_id']], stat_steam_id,
                            stats['current_gold'], stats['current_hp'], stats['max_hp'],
                            stats['damage_taken'], stats['hp_healed'],
                            stats['gold_gained'], stats['gold_lost'], stats['gold_spent'], stats['gold_stolen'],
                            stats.get('max_hp_gained', 0), stats.get('max_hp_lost', 0),
                        ))
                        ps_id = cur.fetchone()[0]
                        _insert_stat_details(cur, ps_id, stats)


def _insert_stat_details(cur, ps_id, stats):
    for c in stats.get('card_choices', []):
        cur.execute("""
            INSERT INTO card_choices (player_stats_id, card_id, floor_added_to_deck, current_upgrade_level, was_picked)
            VALUES (%s, %s, %s, %s, %s)
        """, (ps_id, c['card']['id'], c['card'].get('floor_added_to_deck'), c['card'].get('current_upgrade_level'), c['was_picked']))

    for c in stats.get('relic_choices', []):
        cur.execute(
            "INSERT INTO relic_choices (player_stats_id, relic_id, was_picked) VALUES (%s, %s, %s)",
            (ps_id, c['choice'], c['was_picked']),
        )

    for c in stats.get('potion_choices', []):
        cur.execute(
            "INSERT INTO potion_choices (player_stats_id, potion_id, was_picked) VALUES (%s, %s, %s)",
            (ps_id, c['choice'], c['was_picked']),
        )

    for c in stats.get('ancient_choice', []):
        cur.execute("""
            INSERT INTO ancient_choices (player_stats_id, text_key, title_key, title_table, was_chosen)
            VALUES (%s, %s, %s, %s, %s)
        """, (ps_id, c['TextKey'], c['title']['key'], c['title']['table'], c['was_chosen']))

    for i, c in enumerate(stats.get('event_choices', [])):
        cur.execute("""
            INSERT INTO event_choices (player_stats_id, choice_order, title_key, title_table)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (ps_id, i, c['title']['key'], c['title']['table']))
        ec_id = cur.fetchone()[0]
        for var_name, var in c.get('variables', {}).items():
            cur.execute("""
                INSERT INTO event_choice_variables (event_choice_id, var_name, var_type, decimal_value, bool_value, string_value)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (ec_id, var_name, var.get('type'), var.get('decimal_value'), var.get('bool_value'), var.get('string_value')))

    for i, choice in enumerate(stats.get('rest_site_choices', [])):
        cur.execute(
            "INSERT INTO rest_site_choices (player_stats_id, choice_order, choice) VALUES (%s, %s, %s)",
            (ps_id, i, choice),
        )

    for c in stats.get('cards_gained', []):
        enc = c.get('enchantment') or {}
        cur.execute("""
            INSERT INTO stat_cards_gained (
                player_stats_id, card_id, floor_added_to_deck, current_upgrade_level,
                enchantment_id, enchantment_amount
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (ps_id, c['id'], c.get('floor_added_to_deck'), c.get('current_upgrade_level'), enc.get('id'), enc.get('amount')))

    for c in stats.get('cards_removed', []):
        cur.execute(
            "INSERT INTO stat_cards_removed (player_stats_id, card_id, floor_added_to_deck) VALUES (%s, %s, %s)",
            (ps_id, c['id'], c.get('floor_added_to_deck')),
        )

    for c in stats.get('cards_transformed', []):
        cur.execute("""
            INSERT INTO stat_cards_transformed (
                player_stats_id, original_card_id, original_floor_added_to_deck,
                final_card_id, final_floor_added_to_deck
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            ps_id,
            c['original_card']['id'], c['original_card'].get('floor_added_to_deck'),
            c['final_card']['id'], c['final_card'].get('floor_added_to_deck'),
        ))

    for c in stats.get('cards_enchanted', []):
        enc = c['card'].get('enchantment') or {}
        cur.execute("""
            INSERT INTO stat_cards_enchanted (
                player_stats_id, card_id, floor_added_to_deck, current_upgrade_level,
                enchantment_id, enchantment_amount
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            ps_id, c['card']['id'], c['card'].get('floor_added_to_deck'), c['card'].get('current_upgrade_level'),
            enc.get('id'), enc.get('amount'),
        ))

    for card_id in stats.get('upgraded_cards', []):
        cur.execute(
            "INSERT INTO stat_cards_upgraded (player_stats_id, card_id) VALUES (%s, %s)",
            (ps_id, card_id),
        )

    for potion_id in stats.get('potion_used', []):
        cur.execute(
            "INSERT INTO stat_potions_used (player_stats_id, potion_id) VALUES (%s, %s)",
            (ps_id, potion_id),
        )

    for potion_id in stats.get('potion_discarded', []):
        cur.execute(
            "INSERT INTO stat_potions_discarded (player_stats_id, potion_id) VALUES (%s, %s)",
            (ps_id, potion_id),
        )

    for card_id in stats.get('bought_colorless', []):
        cur.execute(
            "INSERT INTO stat_bought_colorless (player_stats_id, card_id) VALUES (%s, %s)",
            (ps_id, card_id),
        )


def grab_run_files():
    """Return sorted list of (path, steam_id) for all run files across all Steam user directories."""
    results = []
    for steam_dir in STS2_STEAM_ROOT.iterdir():
        if not steam_dir.is_dir():
            continue
        history_dir = steam_dir / "profile1/saves/history"
        if history_dir.is_dir():
            steam_id = int(steam_dir.name)
            for f in history_dir.glob("*.run"):
                results.append((f, steam_id))
    return sorted(results, key=lambda x: x[0].name)



if __name__ == "__main__":

    run_files = grab_run_files()
    print(f"Found {len(run_files)} run files.")

    try:
        conn = connect_db()
    except KeyError as e:
        print(f"Missing environment variable: {e}")
        raise SystemExit(1)

    inserted = 0
    skipped = 0
    errors = 0

    for f, steam_id in run_files:
        try:
            with open(f) as fh:
                run_data = json.load(fh)
            parsed = parse_run(run_data)
            parsed['map_point_history'] = handle_map_point_history(parsed['map_point_history'])
            parsed['players'] = [handle_players(p) for p in parsed['players']]
            if run_exists(conn, parsed):
                skipped += 1
                print(f"  [SKIP]    {f.name}  (already in DB)")
                continue
            insert_run(conn, parsed, steam_id)
            inserted += 1
            print(f"  [OK]      {f.name}")
        except Exception as e:
            errors += 1
            print(f"  [ERROR]   {f.name}  {e}")

    conn.close()
    print(f"\nDone. {inserted} inserted, {skipped} skipped, {errors} errors.")
