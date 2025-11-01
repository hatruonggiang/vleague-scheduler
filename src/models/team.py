from dataclasses import dataclass
from typing import Optional

@dataclass
class Team:
    """
    Đại diện cho một đội bóng trong V.League
    """
    id: int
    name: str
    short_name: str
    city: str
    home_stadium_id: int
    
    def __str__(self) -> str:
        return f"{self.short_name} ({self.city})"
    
    def __repr__(self) -> str:
        return f"Team(id={self.id}, name='{self.name}')"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Team):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)