from typing import List, Dict, Tuple
from ..models.team import Team
from ..models.stadium import Stadium
from ..models.match import Match

class DataPreprocessor:
    """
    Tiền xử lý dữ liệu, tạo danh sách tất cả các trận đấu có thể
    """
    
    def __init__(self, teams: List[Team], stadiums: List[Stadium]):
        self.teams = teams
        self.stadiums = stadiums
        self.teams_dict = {team.id: team for team in teams}
        self.stadiums_dict = {stadium.id: stadium for stadium in stadiums}
    
    def generate_all_matches(self) -> List[Match]:
        """
        Tạo danh sách tất cả các trận đấu theo thể thức vòng tròn 2 lượt
        
        Với n đội, mỗi đội đấu với (n-1) đội khác 2 lần (home và away)
        Tổng số trận: n * (n-1) = 14 * 13 = 182 trận
        """
        all_matches = []
        match_id = 1
        
        n_teams = len(self.teams)
        
        # Duyệt qua tất cả các cặp đội
        for i in range(n_teams):
            for j in range(n_teams):
                if i != j:  # Đội không tự đấu với chính mình
                    home_team = self.teams[i]
                    away_team = self.teams[j]
                    
                    # Tạo trận đấu với sân nhà của home_team
                    match = Match(
                        id=match_id,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        stadium_id=home_team.home_stadium_id,
                        round_number=0  # Chưa phân vòng
                    )
                    all_matches.append(match)
                    match_id += 1
        
        return all_matches
    
    def get_matchup_pairs(self) -> List[Tuple[int, int]]:
        """
        Lấy danh sách các cặp đấu (không phân biệt home/away)
        
        Returns: List of (team1_id, team2_id) với team1_id < team2_id
        """
        pairs = []
        n_teams = len(self.teams)
        
        for i in range(n_teams):
            for j in range(i + 1, n_teams):
                pairs.append((self.teams[i].id, self.teams[j].id))
        
        return pairs
    
    def get_team_opponents(self, team_id: int) -> List[int]:
        """
        Lấy danh sách ID các đội đối thủ của một đội
        """
        opponents = []
        for team in self.teams:
            if team.id != team_id:
                opponents.append(team.id)
        return opponents
    
    def get_teams_sharing_stadium(self) -> Dict[int, List[int]]:
        """
        Lấy danh sách các đội dùng chung sân
        
        Returns: Dict với key là stadium_id, value là list các team_id
        """
        stadium_teams = {}
        
        for team in self.teams:
            stadium_id = team.home_stadium_id
            if stadium_id not in stadium_teams:
                stadium_teams[stadium_id] = []
            stadium_teams[stadium_id].append(team.id)
        
        # Chỉ giữ lại các sân có nhiều hơn 1 đội
        shared_stadiums = {sid: teams for sid, teams in stadium_teams.items() if len(teams) > 1}
        
        return shared_stadiums
    
    def calculate_total_rounds(self) -> int:
        """
        Tính tổng số vòng đấu cần thiết
        
        Với n đội (chẵn), số vòng = 2 * (n - 1)
        Với 14 đội: 2 * 13 = 26 vòng
        """
        n_teams = len(self.teams)
        return 2 * (n_teams - 1)
    
    def get_matches_per_round(self) -> int:
        """
        Số trận mỗi vòng
        
        Với n đội: n/2 trận mỗi vòng
        Với 14 đội: 7 trận/vòng
        """
        return len(self.teams) // 2
    
    def create_team_index_mapping(self) -> Dict[int, int]:
        """
        Tạo mapping từ team_id sang index (0 đến n-1)
        Hữu ích cho các thuật toán matrix-based
        """
        return {team.id: idx for idx, team in enumerate(self.teams)}
    
    def create_reverse_team_mapping(self) -> Dict[int, int]:
        """
        Tạo mapping từ index sang team_id
        """
        return {idx: team.id for idx, team in enumerate(self.teams)}
    
    def get_statistics(self) -> Dict:
        """
        Lấy thống kê về dữ liệu
        """
        shared_stadiums = self.get_teams_sharing_stadium()
        
        stats = {
            'total_teams': len(self.teams),
            'total_stadiums': len(self.stadiums),
            'total_matches': len(self.teams) * (len(self.teams) - 1),
            'total_rounds': self.calculate_total_rounds(),
            'matches_per_round': self.get_matches_per_round(),
            'total_matchups': len(self.get_matchup_pairs()),
            'shared_stadiums': len(shared_stadiums),
            'teams_sharing_stadiums': sum(len(teams) for teams in shared_stadiums.values())
        }
        
        return stats
    
    def print_statistics(self) -> None:
        """
        In thống kê dữ liệu
        """
        stats = self.get_statistics()
        
        print("=" * 50)
        print("THỐNG KÊ DỮ LIỆU:")
        print(f"Số đội: {stats['total_teams']}")
        print(f"Số sân: {stats['total_stadiums']}")
        print(f"Tổng số trận: {stats['total_matches']}")
        print(f"Số vòng đấu: {stats['total_rounds']}")
        print(f"Số trận mỗi vòng: {stats['matches_per_round']}")
        print(f"Số cặp đấu: {stats['total_matchups']}")
        print(f"Số sân dùng chung: {stats['shared_stadiums']}")
        print(f"Số đội dùng chung sân: {stats['teams_sharing_stadiums']}")
        print("=" * 50)
        
        # In chi tiết các sân dùng chung
        shared_stadiums = self.get_teams_sharing_stadium()
        if shared_stadiums:
            print("\nCÁC SÂN DÙNG CHUNG:")
            for stadium_id, team_ids in shared_stadiums.items():
                stadium = self.stadiums_dict[stadium_id]
                team_names = [self.teams_dict[tid].short_name for tid in team_ids]
                print(f"  {stadium.name}: {', '.join(team_names)}")