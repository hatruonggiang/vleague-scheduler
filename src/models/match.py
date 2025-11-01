from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Match:
    """
    Đại diện cho một trận đấu
    """
    id: int
    home_team_id: int
    away_team_id: int
    stadium_id: int
    round_number: int  # Vòng đấu (1-26 cho 14 đội)
    match_date: Optional[datetime] = None
    match_time: Optional[str] = None  # VD: "19:00"
    
    def __str__(self) -> str:
        return f"Round {self.round_number}: Team {self.home_team_id} vs Team {self.away_team_id}"
    
    def __repr__(self) -> str:
        return f"Match(id={self.id}, home={self.home_team_id}, away={self.away_team_id}, round={self.round_number})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Match):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def get_teams(self) -> tuple:
        """Trả về tuple (home_team_id, away_team_id)"""
        return (self.home_team_id, self.away_team_id)
    
    def involves_team(self, team_id: int) -> bool:
        """Kiểm tra trận đấu có liên quan đến đội nào không"""
        return team_id in (self.home_team_id, self.away_team_id)
    
    def is_same_matchup(self, other) -> bool:
        """Kiểm tra 2 trận có cùng cặp đấu không (bất kể home/away)"""
        if not isinstance(other, Match):
            return False
        teams1 = set([self.home_team_id, self.away_team_id])
        teams2 = set([other.home_team_id, other.away_team_id])
        return teams1 == teams2