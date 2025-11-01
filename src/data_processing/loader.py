import pandas as pd
from typing import List, Dict
from ..models.team import Team
from ..models.stadium import Stadium

class DataLoader:
    """
    Load dữ liệu từ các file CSV
    """
    
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = data_dir
    
    def load_teams(self, filename: str = "teams.csv") -> List[Team]:
        """
        Load danh sách đội bóng từ CSV
        
        CSV format:
        id,name,short_name,city,home_stadium_id
        """
        filepath = f"{self.data_dir}/{filename}"
        df = pd.read_csv(filepath)
        
        teams = []
        for _, row in df.iterrows():
            team = Team(
                id=int(row['id']),
                name=str(row['name']),
                short_name=str(row['short_name']),
                city=str(row['city']),
                home_stadium_id=int(row['home_stadium_id'])
            )
            teams.append(team)
        
        return teams
    
    def load_stadiums(self, filename: str = "stadiums.csv") -> List[Stadium]:
        """
        Load danh sách sân vận động từ CSV
        
        CSV format:
        id,name,city,capacity,has_lighting,surface_type
        """
        filepath = f"{self.data_dir}/{filename}"
        df = pd.read_csv(filepath)
        
        stadiums = []
        for _, row in df.iterrows():
            stadium = Stadium(
                id=int(row['id']),
                name=str(row['name']),
                city=str(row['city']),
                capacity=int(row['capacity']),
                has_lighting=bool(row['has_lighting']),
                surface_type=str(row['surface_type'])
            )
            stadiums.append(stadium)
        
        return stadiums
    
    def load_distances(self, filename: str = "distances.csv") -> Dict[tuple, float]:
        """
        Load ma trận khoảng cách giữa các thành phố
        
        CSV format:
        city1,city2,distance_km
        
        Returns: Dict với key là (city1, city2) và value là khoảng cách
        """
        filepath = f"{self.data_dir}/{filename}"
        df = pd.read_csv(filepath)
        
        distances = {}
        for _, row in df.iterrows():
            city1 = str(row['city1'])
            city2 = str(row['city2'])
            distance = float(row['distance_km'])
            
            # Lưu cả 2 chiều
            distances[(city1, city2)] = distance
            distances[(city2, city1)] = distance
        
        return distances
    
    def load_special_dates(self, filename: str = "special_dates.csv") -> List[str]:
        """
        Load danh sách ngày đặc biệt (FIFA Days, ngày lễ, ...)
        
        CSV format:
        date,description
        
        Returns: List các ngày dạng string 'YYYY-MM-DD'
        """
        filepath = f"{self.data_dir}/{filename}"
        df = pd.read_csv(filepath)
        
        special_dates = df['date'].tolist()
        return special_dates
    
    def load_all_data(self) -> Dict:
        """
        Load tất cả dữ liệu cùng lúc
        
        Returns: Dictionary chứa tất cả dữ liệu
        """
        return {
            'teams': self.load_teams(),
            'stadiums': self.load_stadiums(),
            'distances': self.load_distances(),
            'special_dates': self.load_special_dates()
        }