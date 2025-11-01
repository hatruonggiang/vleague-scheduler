from typing import List, Tuple
import random
from ..models.match import Match
from ..models.schedule import Schedule
from ..models.team import Team

class ScheduleEncoding:
    """
    Định nghĩa cách biểu diễn nhiễm sắc thể (chromosome) cho GA
    
    Encoding strategy: Direct encoding
    - Mỗi cá thể là một Schedule chứa list các Match đã được gán vòng đấu
    - Gen = một trận đấu với thông tin vòng đấu
    """
    
    def __init__(self, teams: List[Team]):
        self.teams = teams
        self.n_teams = len(teams)
        self.total_rounds = 2 * (self.n_teams - 1)  # 26 vòng cho 14 đội
        self.matches_per_round = self.n_teams // 2  # 7 trận/vòng
        
    def create_all_possible_matches(self) -> List[Match]:
        """
        Tạo danh sách tất cả các trận đấu có thể (chưa gán vòng)
        
        Returns: List gồm n*(n-1) trận đấu
        """
        all_matches = []
        match_id = 1
        
        for i in range(self.n_teams):
            for j in range(self.n_teams):
                if i != j:
                    home_team = self.teams[i]
                    away_team = self.teams[j]
                    
                    match = Match(
                        id=match_id,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        stadium_id=home_team.home_stadium_id,
                        round_number=0  # Chưa gán vòng
                    )
                    all_matches.append(match)
                    match_id += 1
        
        return all_matches
    
    def encode_schedule_as_list(self, schedule: Schedule) -> List[int]:
        """
        Encode schedule thành list integer (cho một số operators)
        
        List có độ dài = total_rounds * matches_per_round
        Mỗi phần tử là match_id
        
        Returns: List[match_id]
        """
        encoded = []
        
        for round_num in range(1, self.total_rounds + 1):
            round_matches = schedule.get_matches_by_round(round_num)
            round_matches_sorted = sorted(round_matches, key=lambda m: m.id)
            
            for match in round_matches_sorted:
                encoded.append(match.id)
        
        return encoded
    
    def decode_list_to_schedule(self, encoded: List[int], 
                                all_matches: List[Match]) -> Schedule:
        """
        Decode list integer thành Schedule
        
        Args:
            encoded: List match_id đã được sắp xếp theo vòng
            all_matches: Danh sách tất cả trận đấu (để map id -> match)
        
        Returns: Schedule
        """
        match_dict = {match.id: match for match in all_matches}
        schedule = Schedule()
        
        round_num = 1
        for i, match_id in enumerate(encoded):
            if i > 0 and i % self.matches_per_round == 0:
                round_num += 1
            
            original_match = match_dict[match_id]
            new_match = Match(
                id=original_match.id,
                home_team_id=original_match.home_team_id,
                away_team_id=original_match.away_team_id,
                stadium_id=original_match.stadium_id,
                round_number=round_num
            )
            schedule.add_match(new_match)
        
        return schedule
    
    def get_matchup_pair(self, match: Match) -> Tuple[int, int]:
        """
        Lấy cặp đội từ trận đấu (sorted để so sánh)
        
        Returns: (team_id_1, team_id_2) với team_id_1 < team_id_2
        """
        return tuple(sorted([match.home_team_id, match.away_team_id]))
    
    def find_reverse_match(self, match: Match, all_matches: List[Match]) -> Match:
        """
        Tìm trận lượt về tương ứng
        
        Args:
            match: Trận lượt đi (A vs B)
            all_matches: Danh sách tất cả trận
        
        Returns: Trận lượt về (B vs A)
        """
        for m in all_matches:
            if (m.home_team_id == match.away_team_id and 
                m.away_team_id == match.home_team_id):
                return m
        return None
    
    def split_into_legs(self, all_matches: List[Match]) -> Tuple[List[Match], List[Match]]:
        """
        Chia các trận đấu thành 2 lượt (lượt đi và lượt về)
        
        Strategy: Mỗi cặp đấu có 2 trận (A-B và B-A), chia đều vào 2 lượt
        
        Returns: (first_leg_matches, second_leg_matches)
        """
        matchup_dict = {}
        
        # Group matches by matchup pair
        for match in all_matches:
            pair = self.get_matchup_pair(match)
            if pair not in matchup_dict:
                matchup_dict[pair] = []
            matchup_dict[pair].append(match)
        
        first_leg = []
        second_leg = []
        
        for pair, matches in matchup_dict.items():
            if len(matches) == 2:
                # Ngẫu nhiên chọn một trận vào lượt đi, trận còn lại vào lượt về
                random.shuffle(matches)
                first_leg.append(matches[0])
                second_leg.append(matches[1])
        
        return first_leg, second_leg
    
    def create_round_robin_groups(self, teams: List[Team]) -> List[List[Tuple[int, int]]]:
        """
        Tạo các vòng đấu theo thuật toán Round-robin
        
        Thuật toán: Circle method (quay vòng)
        
        Returns: List các vòng, mỗi vòng là list các cặp đấu
        """
        n = len(teams)
        if n % 2 == 1:
            # Thêm "dummy" team nếu số đội lẻ (không xảy ra với 14 đội)
            teams = teams + [None]
            n += 1
        
        rounds = []
        team_indices = list(range(n))
        
        for round_num in range(n - 1):
            round_matches = []
            
            for i in range(n // 2):
                idx1 = team_indices[i]
                idx2 = team_indices[n - 1 - i]
                
                if idx1 is not None and idx2 is not None:
                    team1 = teams[idx1]
                    team2 = teams[idx2]
                    
                    if team1 is not None and team2 is not None:
                        # Luân phiên home/away
                        if round_num % 2 == 0:
                            round_matches.append((team1.id, team2.id))
                        else:
                            round_matches.append((team2.id, team1.id))
            
            rounds.append(round_matches)
            
            # Rotate (giữ đội đầu cố định, quay các đội còn lại)
            team_indices = [team_indices[0]] + [team_indices[-1]] + team_indices[1:-1]
        
        return rounds
    
    def validate_encoding(self, schedule: Schedule) -> bool:
        """
        Kiểm tra cơ bản xem encoding có hợp lệ không
        
        Returns: True nếu cơ bản hợp lệ
        """
        # Kiểm tra số trận
        if len(schedule.matches) != self.n_teams * (self.n_teams - 1):
            return False
        
        # Kiểm tra số vòng
        if schedule.get_total_rounds() != self.total_rounds:
            return False
        
        # Kiểm tra mỗi vòng có đúng số trận
        for round_num in range(1, self.total_rounds + 1):
            round_matches = schedule.get_matches_by_round(round_num)
            if len(round_matches) != self.matches_per_round:
                return False
        
        return True