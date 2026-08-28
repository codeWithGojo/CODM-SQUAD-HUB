# Tournament Operations

Only users with an approved Tournament Organizer application (or platform admins) can create tournaments. Ownership remains scoped to the creating organizer.

The enforced lifecycle is:

`draft → registration → roster_locked → live → completed → archived`

Cancellation is allowed before archival. Registration opening/closing, roster lock, start/end order, capacity, roster size, active membership, minor consent, career status, and active CRA sanctions are validated.

Approved registrations feed bracket generation. Participating managers report scores and their own registered-player stats; the organizer verifies the match. Verification creates official ledger records, updates standings and player market values, emits a realtime event, and prevents further edits. Completing a season-linked tournament recalculates that mode's rankings.

Hardpoint player stats can also carry an ordered hill-by-hill kill breakdown and role profile. Squad Hub calculates peak output, average kills per active hill, and a consistency score on a declared shared scale. This detail remains private to the submitting team until the match is verified.

Match disputes freeze verification until the organizer records a ruling. CRA blacklist sanctions can block players, teams, or organizations from tournament registration; eligible subjects can appeal and platform admins can uphold or revoke the sanction.
