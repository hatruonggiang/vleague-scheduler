from typing import List, Dict, Tuple
from ..models.team import Team
from ..models.stadium import Stadium

class DataValidator:
    """
    Validate dữ liệu đầu vào
    """
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_teams(self, teams: List[Team]) -> bool:
        """
        Validate danh sách đội bóng
        """
        self.errors = []
        self.warnings = []
        
        # Kiểm tra số lượng đội
        if len(teams) != 14:
            self.errors.append(f"V.League cần đúng 14 đội, hiện có {len(teams)} đội")
        
        # Kiểm tra ID trùng lặp
        ids = [team.id for team in teams]
        if len(ids) != len(set(ids)):
            self.errors.append("Có ID đội bị trùng lặp")
        
        # Kiểm tra tên trùng lặp
        names = [team.name for team in teams]
        if len(names) != len(set(names)):
            self.warnings.append("Có tên đội bị trùng lặp")
        
        # Kiểm tra short_name trùng lặp
        short_names = [team.short_name for team in teams]
        if len(short_names) != len(set(short_names)):
            self.errors.append("Có tên viết tắt đội bị trùng lặp")
        
        # Kiểm tra các trường bắt buộc
        for team in teams:
            if not team.name or not team.short_name:
                self.errors.append(f"Đội ID {team.id} thiếu tên hoặc tên viết tắt")
            if not team.city:
                self.errors.append(f"Đội {team.short_name} thiếu thông tin thành phố")
            if team.home_stadium_id <= 0:
                self.errors.append(f"Đội {team.short_name} có home_stadium_id không hợp lệ")
        
        return len(self.errors) == 0
    
    def validate_stadiums(self, stadiums: List[Stadium]) -> bool:
        """
        Validate danh sách sân vận động
        """
        self.errors = []
        self.warnings = []
        
        # Kiểm tra ID trùng lặp
        ids = [stadium.id for stadium in stadiums]
        if len(ids) != len(set(ids)):
            self.errors.append("Có ID sân vận động bị trùng lặp")
        
        # Kiểm tra các trường bắt buộc
        for stadium in stadiums:
            if not stadium.name or not stadium.city:
                self.errors.append(f"Sân ID {stadium.id} thiếu tên hoặc thành phố")
            if stadium.capacity <= 0:
                self.errors.append(f"Sân {stadium.name} có sức chứa không hợp lệ")
            if stadium.surface_type not in ['natural', 'artificial']:
                self.errors.append(f"Sân {stadium.name} có loại mặt sân không hợp lệ")
        
        # Warning cho sân không có đèn
        stadiums_no_light = [s.name for s in stadiums if not s.has_lighting]
        if stadiums_no_light:
            self.warnings.append(f"Các sân không có đèn chiếu sáng: {', '.join(stadiums_no_light)}")
        
        return len(self.errors) == 0
    
    def validate_teams_stadiums_mapping(self, teams: List[Team], stadiums: List[Stadium]) -> bool:
        """
        Validate mối quan hệ giữa đội và sân
        """
        self.errors = []
        self.warnings = []
        
        stadium_ids = {stadium.id for stadium in stadiums}
        
        # Kiểm tra mỗi đội có sân nhà hợp lệ
        for team in teams:
            if team.home_stadium_id not in stadium_ids:
                self.errors.append(f"Đội {team.short_name} có home_stadium_id={team.home_stadium_id} không tồn tại")
        
        # Kiểm tra các đội dùng chung sân
        stadium_usage = {}
        for team in teams:
            if team.home_stadium_id not in stadium_usage:
                stadium_usage[team.home_stadium_id] = []
            stadium_usage[team.home_stadium_id].append(team.short_name)
        
        for stadium_id, team_names in stadium_usage.items():
            if len(team_names) > 1:
                stadium = next(s for s in stadiums if s.id == stadium_id)
                self.warnings.append(f"Sân {stadium.name} được dùng chung bởi: {', '.join(team_names)}")
        
        return len(self.errors) == 0
    
    def validate_distances(self, distances: Dict[Tuple[str, str], float], teams: List[Team]) -> bool:
        """
        Validate ma trận khoảng cách
        """
        self.errors = []
        self.warnings = []
        
        cities = set(team.city for team in teams)
        
        # Kiểm tra có đủ khoảng cách giữa các thành phố
        for city1 in cities:
            for city2 in cities:
                if city1 != city2:
                    if (city1, city2) not in distances:
                        self.errors.append(f"Thiếu khoảng cách giữa {city1} và {city2}")
                    elif distances.get((city1, city2), 0) <= 0:
                        self.errors.append(f"Khoảng cách giữa {city1} và {city2} không hợp lệ")
        
        # Kiểm tra tính đối xứng
        for (city1, city2), dist in distances.items():
            reverse_dist = distances.get((city2, city1))
            if reverse_dist is None:
                self.warnings.append(f"Thiếu khoảng cách ngược từ {city2} về {city1}")
            elif abs(dist - reverse_dist) > 1:  # Cho phép sai số 1km
                self.warnings.append(f"Khoảng cách không đối xứng: {city1}-{city2}={dist}km, {city2}-{city1}={reverse_dist}km")
        
        return len(self.errors) == 0
    
    def validate_special_dates(self, special_dates: List[str]) -> bool:
        """
        Validate danh sách ngày đặc biệt
        """
        self.errors = []
        self.warnings = []
        
        # Kiểm tra format ngày
        import re
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        for date_str in special_dates:
            if not date_pattern.match(date_str):
                self.errors.append(f"Ngày '{date_str}' không đúng format YYYY-MM-DD")
        
        # Kiểm tra trùng lặp
        if len(special_dates) != len(set(special_dates)):
            self.warnings.append("Có ngày đặc biệt bị trùng lặp")
        
        return len(self.errors) == 0
    
    def validate_all(self, teams: List[Team], stadiums: List[Stadium], 
                     distances: Dict[Tuple[str, str], float], 
                     special_dates: List[str]) -> bool:
        """
        Validate tất cả dữ liệu
        """
        all_errors = []
        all_warnings = []
        
        # Validate teams
        if not self.validate_teams(teams):
            all_errors.extend(self.errors)
        all_warnings.extend(self.warnings)
        
        # Validate stadiums
        if not self.validate_stadiums(stadiums):
            all_errors.extend(self.errors)
        all_warnings.extend(self.warnings)
        
        # Validate mapping
        if not self.validate_teams_stadiums_mapping(teams, stadiums):
            all_errors.extend(self.errors)
        all_warnings.extend(self.warnings)
        
        # Validate distances
        if not self.validate_distances(distances, teams):
            all_errors.extend(self.errors)
        all_warnings.extend(self.warnings)
        
        # Validate special dates
        if not self.validate_special_dates(special_dates):
            all_errors.extend(self.errors)
        all_warnings.extend(self.warnings)
        
        # Gán lại tất cả errors và warnings
        self.errors = all_errors
        self.warnings = all_warnings
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """Lấy danh sách lỗi"""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """Lấy danh sách cảnh báo"""
        return self.warnings
    
    def print_report(self) -> None:
        """In báo cáo validation"""
        if self.errors:
            print("=" * 50)
            print("LỖI:")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")
        
        if self.warnings:
            print("=" * 50)
            print("CẢNH BÁO:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("=" * 50)
            print("✓ Dữ liệu hợp lệ!")