from models import MatchOutcome

# Rules for each match outcome. To add a new one (e.g. forfeit, bye), add a value
# to MatchOutcome in models.py and an entry here.
#   decided_by_score: winner comes from the score (False = organizer declares it)
#   counts_scores:    scores count towards points scored / conceded in standings
#   reportable:       include the match in the DUPR export
OUTCOME_RULES = {
    MatchOutcome.NORMAL: {'decided_by_score': True, 'counts_scores': True, 'reportable': True},
    MatchOutcome.WALKOVER: {'decided_by_score': False, 'counts_scores': False, 'reportable': False},
}


class OutcomeError(ValueError):
    pass


def get_rule(outcome):
    """Rule for a stored or requested outcome. Missing means normal."""
    try:
        return OUTCOME_RULES[MatchOutcome(outcome or MatchOutcome.NORMAL)]
    except ValueError:
        allowed = ', '.join(o.value for o in MatchOutcome)
        raise OutcomeError(f"Unknown outcome '{outcome}'. Must be one of: {allowed}")


def resolve_result(team1_id, team2_id, team1_score, team2_score, outcome=None, winner_team_id=None):
    """
    Single place that decides a match's result. Returns:
      is_decided   - counts as a completed match in standings
      winner       - winning team id, or None (draw / undecided)
      team1_points, team2_points - points credited to each team in standings
    """
    rule = get_rule(outcome)
    team1_score = team1_score or 0
    team2_score = team2_score or 0

    if rule['decided_by_score']:
        # Existing behaviour: 0-0 = not played, higher score wins, equal = draw
        is_decided = not (team1_score == 0 and team2_score == 0)
        if team1_score > team2_score:
            winner = team1_id
        elif team2_score > team1_score:
            winner = team2_id
        else:
            winner = None
    else:
        winner = winner_team_id if winner_team_id in (team1_id, team2_id) else None
        is_decided = winner is not None

    if not rule['counts_scores']:
        team1_score = team2_score = 0

    return {
        'is_decided': is_decided,
        'winner': winner if is_decided else None,
        'team1_points': team1_score,
        'team2_points': team2_score,
    }


def apply_outcome(match, outcome, winner_team_id=None):
    """
    Set an organizer-declared outcome on a match (caller commits).
    Setting 'normal' resets the match so it can be scored again (undo a walkover).
    """
    rule = get_rule(outcome)

    if rule['decided_by_score']:
        match.outcome = MatchOutcome.NORMAL.value
        match.winner_team_id = None
        match.is_final = False
        match.status = 'pending'
        return

    if not match.team1_id or not match.team2_id:
        raise OutcomeError("Both teams must be set on the match")
    if winner_team_id not in (match.team1_id, match.team2_id):
        raise OutcomeError("winner_team_id must be one of the two teams in the match")

    match.outcome = MatchOutcome(outcome).value
    match.winner_team_id = winner_team_id
    match.is_final = True
    match.status = 'completed'
