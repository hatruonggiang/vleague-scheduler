from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from .match import Match

@dataclass
class Schedule:
    """
    Đại diện cho một lịch thi đấu hoàn chỉnh (một cá thể trong GA)
    """
    matches: List[Match] = field(default_factory=list)
    fitness_score: Optional[float] = None
    
    def __len__(self) -> int:
        return len(self.matches)
    
    def __getitem__(self, index: int) -> Match:
        return self.matches[index]
    
    def __iter__(self):
        return iter(self.matches)
    
    def add_match(self, match: Match) -> None:
        """Thêm một trận đấu vào lịch"""
        self.matches.append(match)
    
    def get_matches_by_round(self, round_number: int) -> List[Match]:
        """Lấy tất cả trận đấu trong một vòng"""
        return [m for m in self.matches if m.round_number == round_number]
    
    def get_matches_by_team(self, team_id: int) -> List[Match]:
        """Lấy tất cả trận đấu của một đội"""
        return [m for m in self.matches if m.involves_team(team_id)]
    
    def get_home_matches(self, team_id: int) -> List[Match]:
        """Lấy tất cả trận sân nhà của một đội"""
        return [m for m in self.matches if m.home_team_id == team_id]
    
    def get_away_matches(self, team_id: int) -> List[Match]:
        """Lấy tất cả trận sân khách của một đội"""
        return [m for m in self.matches if m.away_team_id == team_id]
    
    def get_total_rounds(self) -> int:
        """Lấy tổng số vòng đấu"""
        if not self.matches:
            return 0
        return max(m.round_number for m in self.matches)
    
    def get_matches_at_stadium(self, stadium_id: int, round_number: int) -> List[Match]:
        """Lấy các trận đấu tại một sân trong một vòng đấu"""
        return [m for m in self.matches 
                if m.stadium_id == stadium_id and m.round_number == round_number]
    
    def clone(self) -> 'Schedule':
        """Tạo bản sao của lịch thi đấu"""
        new_matches = [Match(
            id=m.id,
            home_team_id=m.home_team_id,
            away_team_id=m.away_team_id,
            stadium_id=m.stadium_id,
            round_number=m.round_number,
            match_date=m.match_date,
            match_time=m.match_time
        ) for m in self.matches]
        return Schedule(matches=new_matches, fitness_score=self.fitness_score)
    
    def __str__(self) -> str:
        return f"Schedule({len(self.matches)} matches, {self.get_total_rounds()} rounds, fitness={self.fitness_score})"
    
    def __repr__(self) -> str:
        return self.__str__()