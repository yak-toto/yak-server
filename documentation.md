# Documentation

## User types

### Admin

Needed attributes

- name
- password
- refresh_tokens

### Competition results

- name
- password
- lobby_id (1 to n)
- matches
- competition
- refresh_tokens

### User

- name
- first_name
- last_name
- password
- points etc
- lobby_id (n to 1)
- matches
- refresh_tokens

## Endpoint access

bets: user and competition results (per user)
binary bets: user and competition results (per user)
groups: all (informative)
lobby: admin only
phases: all (informative)
results: user (per lobby)
rules: ?
score bets: user and competition results (per user)
teams: all (informative)
users: all (signup can only create user)

All informative can be removed

## Table structure
