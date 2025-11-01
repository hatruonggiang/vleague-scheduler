import random
from typing import List, Set, Tuple, Dict
from ..models.schedule import Schedule
from ..models.match import Match
from ..models.team import Team

class ScheduleRepairer:
    """
    Sửa chữa các lịch thi đấu không hợp lệ
    """
    
    def __init__(self, teams: List[Team], shared_stadiums: Dict[int, List[int]]):
        self.teams = teams
        self.teams_dict = {team.id: team for team in teams}
        self.shared_stadiums = shared_stadiums
        self.n_teams = len(teams)
        self.total_rounds = 2 * (self.n_teams - 1)
        self.matches_per_round = self.n_teams // 2
    
    def repair_schedule(self, schedule: Schedule, max_iterations: int = 100) -> Schedule:
        """
        Sửa chữa lịch thi đấu không hợp lệ
        
        Thực hiện các bước sửa chữa theo thứ tự:
        1. Đảm bảo đủ số trận
        2. Đảm bảo mỗi đội chỉ đá 1 trận/vòng
        3. Đảm bảo không có 2 đội gặp nhau liên tiếp
        4. Đảm bảo không xung đột sân dùng chung
        
        Args:
            schedule: Schedule cần sửa
            max_iterations: Số lần thử tối đa
        
        Returns: Repaired schedule
        """
        repaired = schedule.clone()
        
        # Bước 1: Đảm bảo có đủ tất cả các trận đấu
        repaired = self._ensure_all_matchups(repaired)
        
        # Bước 2: Đảm bảo mỗi đội chỉ đá 1 trận/vòng
        for _ in range(max_iterations):
            if self._check_one_match_per_team_per_round(repaired):
                break
            repaired = self._fix_one_match_per_round(repaired)
        
        # Bước 3: Đảm bảo không có đối thủ liên tiếp
        for _ in range(max_iterations):
            if self._check_no_consecutive_opponents(repaired):
                break
            repaired = self._fix_consecutive_opponents(repaired)
        
        # Bước 4: Đảm bảo không xung đột sân
        for _ in range(max_iterations):
            if self._check_stadium_conflicts(repaired):
                break
            repaired = self._fix_stadium_conflicts(repaired)
        
        return repaired
    
    def _ensure_all_matchups(self, schedule: Schedule) -> Schedule:
        """
        Đảm bảo có đủ tất cả các cặp đấu (mỗi cặp đúng 2 lần)
        """
        # Tạo dict đếm số lần mỗi cặp xuất hiện
        matchup_count = {}
        existing_matches = []
        
        for match in schedule.matches:
            key = (match.home_team_id, match.away_team_id)
            matchup_count[key] = matchup_count.get(key, 0) + 1
            existing_matches.append(match)
        
        # Tạo list các trận cần thêm
        matches_to_add = []
        match_id = len(existing_matches) + 1
        
        for i in range(self.n_teams):
            for j in range(self.n_teams):
                if i != j:
                    team_i = self.teams[i].id
                    team_j = self.teams[j].id
                    key = (team_i, team_j)
                    
                    count = matchup_count.get(key, 0)
                    
                    # Thêm nếu thiếu
                    if count == 0:
                        home_team = self.teams[i]
                        match = Match(
                            id=match_id,
                            home_team_id=team_i,
                            away_team_id=team_j,
                            stadium_id=home_team.home_stadium_id,
                            round_number=random.randint(1, self.total_rounds)
                        )
                        matches_to_add.append(match)
                        match_id += 1
        
        # Tạo schedule mới
        new_schedule = Schedule()
        for match in existing_matches:
            new_schedule.add_match(match)
        for match in matches_to_add:
            new_schedule.add_match(match)
        
        return new_schedule
    
    def _check_one_match_per_team_per_round(self, schedule: Schedule) -> bool:
        """
        Kiểm tra mỗi đội chỉ đá 1 trận/vòng
        """
        for round_num in range(1, self.total_rounds + 1):
            round_matches = schedule.get_matches_by_round(round_num)
            teams_in_round = []
            
            for match in round_matches:
                teams_in_round.append(match.home_team_id)
                teams_in_round.append(match.away_team_id)
            
            # Kiểm tra có đội nào xuất hiện > 1 lần
            if len(teams_in_round) != len(set(teams_in_round)):
                return False
        
        return True
    
    def _fix_one_match_per_round(self, schedule: Schedule) -> Schedule:
        """
        Sửa vi phạm mỗi đội chỉ đá 1 trận/vòng
        """
        repaired = schedule.clone()
        
        for round_num in range(1, self.total_rounds + 1):
            round_matches = repaired.get_matches_by_round(round_num)
            teams_count = {}
            
            for match in round_matches:
                teams_count[match.home_team_id] = teams_count.get(match.home_team_id, 0) + 1
                teams_count[match.away_team_id] = teams_count.get(match.away_team_id, 0) + 1
            
            # Tìm các đội vi phạm
            violating_teams = [team_id for team_id, count in teams_count.items() if count > 1]
            
            if violating_teams:
                # Di chuyển một số trận sang vòng khác
                for match in round_matches[:]:
                    if match.home_team_id in violating_teams or match.away_team_id in violating_teams:
                        # Tìm vòng khác để di chuyển
                        new_round = self._find_available_round(repaired, match)
                        match.round_number = new_round
                        break
        
        return repaired
    
    def _find_available_round(self, schedule: Schedule, match: Match) -> int:
        """
        Tìm vòng có thể xếp trận này mà không vi phạm
        """
        for round_num in range(1, self.total_rounds + 1):
            round_matches = schedule.get_matches_by_round(round_num)
            teams_in_round = set()
            
            for m in round_matches:
                teams_in_round.add(m.home_team_id)
                teams_in_round.add(m.away_team_id)
            
            # Kiểm tra có thể thêm trận này không
            if (match.home_team_id not in teams_in_round and
                match.away_team_id not in teams_in_round):
                return round_num
        
        # Không tìm thấy vòng phù hợp, trả về vòng ngẫu nhiên
        return random.randint(1, self.total_rounds)
    
    def _check_no_consecutive_opponents(self, schedule: Schedule) -> bool:
        """
        Kiểm tra 2 đội không gặp nhau ở 2 vòng liên tiếp
        """
        for round_num in range(1, self.total_rounds):
            current_round = schedule.get_matches_by_round(round_num)
            next_round = schedule.get_matches_by_round(round_num + 1)
            
            current_matchups = set()
            for match in current_round:
                pair = tuple(sorted([match.home_team_id, match.away_team_id]))
                current_matchups.add(pair)
            
            for match in next_round:
                pair = tuple(sorted([match.home_team_id, match.away_team_id]))
                if pair in current_matchups:
                    return False
        
        return True
    
    def _fix_consecutive_opponents(self, schedule: Schedule) -> Schedule:
        """
        Sửa vi phạm đối thủ liên tiếp
        """
        repaired = schedule.clone()
        
        for round_num in range(1, self.total_rounds):
            current_round = repaired.get_matches_by_round(round_num)
            next_round = repaired.get_matches_by_round(round_num + 1)
            
            current_matchups = {}
            for match in current_round:
                pair = tuple(sorted([match.home_team_id, match.away_team_id]))
                current_matchups[pair] = match
            
            for match in next_round[:]:
                pair = tuple(sorted([match.home_team_id, match.away_team_id]))
                if pair in current_matchups:
                    # Swap với trận khác ở vòng sau
                    other_rounds = list(range(round_num + 2, self.total_rounds + 1))
                    if other_rounds:
                        target_round = random.choice(other_rounds)
                        target_matches = repaired.get_matches_by_round(target_round)
                        
                        if target_matches:
                            swap_match = random.choice(target_matches)
                            
                            # Swap round_number
                            temp = match.round_number
                            match.round_number = swap_match.round_number
                            swap_match.round_number = temp
        
        return repaired
    
    def _check_stadium_conflicts(self, schedule: Schedule) -> bool:
        """
        Kiểm tra không có xung đột sân dùng chung
        """
        if not self.shared_stadiums:
            return True
        
        for round_num in range(1, self.total_rounds + 1):
            round_matches = schedule.get_matches_by_round(round_num)
            stadium_usage = {}
            
            for match in round_matches:
                stadium_id = match.stadium_id
                if stadium_id not in stadium_usage:
                    stadium_usage[stadium_id] = []
                stadium_usage[stadium_id].append(match.home_team_id)
            
            # Kiểm tra các sân dùng chung
            for stadium_id, teams_using in stadium_usage.items():
                if stadium_id in self.shared_stadiums and len(teams_using) > 1:
                    return False
        
        return True
    
    def _fix_stadium_conflicts(self, schedule: Schedule) -> Schedule:
        """
        Sửa xung đột sân dùng chung
        """
        repaired = schedule.clone()
        
        for round_num in range(1, self.total_rounds + 1):
            round_matches = repaired.get_matches_by_round(round_num)
            stadium_usage = {}
            
            for match in round_matches:
                stadium_id = match.stadium_id
                if stadium_id not in stadium_usage:
                    stadium_usage[stadium_id] = []
                stadium_usage[stadium_id].append(match)
            
            # Sửa xung đột
            for stadium_id, matches in stadium_usage.items():
                if stadium_id in self.shared_stadiums and len(matches) > 1:
                    # Giữ lại 1 trận, di chuyển các trận khác
                    for match in matches[1:]:
                        new_round = self._find_round_without_stadium_conflict(
                            repaired, match, stadium_id
                        )
                        match.round_number = new_round
        
        return repaired
    
    def _find_round_without_stadium_conflict(self, schedule: Schedule, 
                                            match: Match, stadium_id: int) -> int:
        """
        Tìm vòng không có xung đột sân
        """
        for round_num in range(1, self.total_rounds + 1):
            round_matches = schedule.get_matches_by_round(round_num)
            
            # Kiểm tra sân này đã được dùng chưa
            stadium_used = any(m.stadium_id == stadium_id for m in round_matches)
            
            # Kiểm tra đội có thi đấu ở vòng này chưa
            teams_in_round = set()
            for m in round_matches:
                teams_in_round.add(m.home_team_id)
                teams_in_round.add(m.away_team_id)
            
            if (not stadium_used and 
                match.home_team_id not in teams_in_round and
                match.away_team_id not in teams_in_round):
                return round_num
        
        # Không tìm thấy, trả về ngẫu nhiên
        return random.randint(1, self.total_rounds)
    
    def quick_repair(self, schedule: Schedule) -> Schedule:
        """
        Sửa nhanh các vi phạm cơ bản nhất
        
        Chỉ sửa những vi phạm nghiêm trọng, nhanh chóng
        """
        repaired = schedule.clone()
        
        # Chỉ sửa vi phạm mỗi đội 1 trận/vòng
        repaired = self._fix_one_match_per_round(repaired)
        
        return repaired