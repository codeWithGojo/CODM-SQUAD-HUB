# Seasonal Ranking Engine

The engine produces separate Multiplayer and Battle Royale tables for players, teams, and organizations. Every calculation writes immutable snapshots for country, African region, and continental (`AFRICA`) scopes.

## Trusted inputs

- Organizer-verified tournament matches inside the season date range
- Bilaterally confirmed team challenges inside the season date range
- Verified tournament player-stat lines for player rankings

Scrims and personal match logs never affect official rankings.

## Team rating

Teams start at 1500. A verified match uses Elo with base K = 32.

- Tournament weight is set between 0.1 and 5.0.
- Finals use 1.25x, semifinals 1.12x, and quarterfinals 1.06x.
- Recency has a 180-day half-life with a 0.20 floor.
- Confirmed challenges use a fixed 0.5 event weight.

## Player rating

Players start at 1000. Each verified tournament stat line adds a bounded contribution derived from kills, assists, deaths, objective score, MVP status, match result, and event weight. The contribution is stored in the snapshot explanation so the table remains explainable.

## Organization rating

An organization's rating is the mean of its two highest-rated active teams in the selected mode. Its country comes from the organization profile and its African zone comes from the seeded region directory. Organization roster tier (T1-T4) does not override competitive performance.

## Snapshots and movement

Each recalculation closes the previous current snapshots, writes a new calculation ID, orders ties deterministically by entity ID, and stores previous rank plus movement. History remains available at `/api/v1/rankings/{entity_type}/{entity_id}/history`.

## Triggers

Approved organizers or platform admins can call `POST /api/v1/rankings/recalculate`. Completing a tournament tied to a season also recalculates that tournament's mode before committing the completion transition.

`GET /api/v1/rankings/formula` publishes the active version (`elo-v1`) and major factors.

## Known limits

- This is a deterministic pilot formula, not an ML predictor.
- Player contributions need more clan/tournament data for calibration across MP roles and BR placements.
- Corrections currently require fixing the verified source and recalculating; a dedicated ranking appeal workflow is future work.
