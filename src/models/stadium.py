from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Stadium:
    """
    Đại diện cho một sân vận động
    """
    id: int
    name: str
    city: str
    capacity: int
    has_lighting: bool  # Có hệ thống đèn chiếu sáng (đá tối được)
    surface_type: str  # 'natural' hoặc 'artificial'
    
    def __str__(self) -> str:
        return f"{self.name} ({self.city})"
    
    def __repr__(self) -> str:
        return f"Stadium(id={self.id}, name='{self.name}')"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Stadium):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def can_host_night_match(self) -> bool:
        """Kiểm tra sân có thể tổ chức trận tối không"""
        return self.has_lighting