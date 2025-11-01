#!/usr/bin/env python3
"""
Script export lịch thi đấu ra file Excel
"""

import sys
import os
from pathlib import Path

# Thêm thư mục gốc vào path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.data_processing.loader import DataLoader
from src.models.schedule import Schedule
from src.models.match import Match
import json
import pandas as pd
from datetime import datetime, timedelta

def load_schedule_from_json(json_path: str) -> Schedule:
    """
    Load schedule từ file JSON
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    schedule = Schedule()
    
    for match_data in data['matches']:
        match = Match(
            id=match_data['id'],
            home_team_id=match_data['home_team_id'],
            away_team_id=match_data['away_team_id'],
            stadium_id=match_data['stadium_id'],
            round_number=match_data['round']
        )
        schedule.add_match(match)
    
    if 'metadata' in data and 'fitness_score' in data['metadata']:
        schedule.fitness_score = data['metadata']['fitness_score']
    
    return schedule

def export_schedule_to_excel(schedule: Schedule, 
                             teams: list, 
                             stadiums: list,
                             output_path: str,
                             start_date: str = "2025-02-15"):
    """
    Export lịch thi đấu ra Excel với format đẹp
    
    Args:
        schedule: Schedule object
        teams: List các Team
        stadiums: List các Stadium
        output_path: Đường dẫn file output
        start_date: Ngày bắt đầu mùa giải (YYYY-MM-DD)
    """
    # Tạo dict để tra cứu
    teams_dict = {team.id: team for team in teams}
    stadiums_dict = {stadium.id: stadium for stadium in stadiums}
    
    # Tạo dữ liệu cho Excel
    data = []
    
    # Giả sử mỗi vòng cách nhau 1 tuần
    start = datetime.strptime(start_date, "%Y-%m-%d")
    
    for match in sorted(schedule.matches, key=lambda m: (m.round_number, m.id)):
        home_team = teams_dict[match.home_team_id]
        away_team = teams_dict[match.away_team_id]
        stadium = stadiums_dict[match.stadium_id]
        
        # Tính ngày thi đấu
        match_date = start + timedelta(weeks=match.round_number - 1)
        
        data.append({
            'Vòng': match.round_number,
            'Ngày': match_date.strftime("%d/%m/%Y"),
            'Thứ': match_date.strftime("%A"),
            'Giờ': '19:00',  # Mặc định
            'Đội nhà': home_team.short_name,
            'Đội khách': away_team.short_name,
            'Sân vận động': stadium.name,
            'Thành phố': stadium.city,
            'ID': match.id
        })
    
    # Tạo DataFrame
    df = pd.DataFrame(data)
    
    # Export ra Excel với formatting
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: Toàn bộ lịch
        df.to_excel(writer, sheet_name='Lịch thi đấu', index=False)
        
        # Sheet 2: Lịch theo từng vòng
        for round_num in range(1, schedule.get_total_rounds() + 1):
            round_df = df[df['Vòng'] == round_num].copy()
            round_df = round_df.drop('Vòng', axis=1)
            sheet_name = f'Vòng {round_num}'
            round_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Sheet 3: Lịch từng đội
        for team in teams:
            team_matches = []
            for match in schedule.matches:
                if match.home_team_id == team.id or match.away_team_id == team.id:
                    home_team = teams_dict[match.home_team_id]
                    away_team = teams_dict[match.away_team_id]
                    stadium = stadiums_dict[match.stadium_id]
                    match_date = start + timedelta(weeks=match.round_number - 1)
                    
                    venue = "Nhà" if match.home_team_id == team.id else "Khách"
                    opponent = away_team.short_name if match.home_team_id == team.id else home_team.short_name
                    
                    team_matches.append({
                        'Vòng': match.round_number,
                        'Ngày': match_date.strftime("%d/%m/%Y"),
                        'Sân': venue,
                        'Đối thủ': opponent,
                        'Địa điểm': stadium.name
                    })
            
            team_df = pd.DataFrame(team_matches)
            sheet_name = team.short_name[:31]  # Excel giới hạn 31 ký tự
            team_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Format các sheet
        workbook = writer.book
        
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            
            # Auto-adjust column width
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Bold header
            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)
    
    print(f"✓ Đã export ra Excel: {output_path}")

def main():
    """
    Main function
    """
    print("=" * 70)
    print("EXPORT LỊCH THI ĐẤU RA EXCEL")
    print("=" * 70)
    
    # 1. Chọn file JSON
    print("\n[1/3] CHỌN FILE JSON")
    print("-" * 70)
    
    schedules_dir = Path("outputs/schedules")
    
    if not schedules_dir.exists():
        print("✗ Thư mục outputs/schedules không tồn tại!")
        return
    
    json_files = list(schedules_dir.glob("*.json"))
    
    if not json_files:
        print("✗ Không tìm thấy file JSON nào!")
        return
    
    print("Các file JSON có sẵn:")
    for i, file in enumerate(json_files, 1):
        print(f"{i}. {file.name}")
    
    choice = input(f"\nChọn file (1-{len(json_files)}) [1]: ").strip() or "1"
    
    try:
        selected_file = json_files[int(choice) - 1]
    except:
        print("✗ Lựa chọn không hợp lệ!")
        return
    
    print(f"✓ Đã chọn: {selected_file.name}")
    
    # 2. Load dữ liệu
    print("\n[2/3] LOAD DỮ LIỆU")
    print("-" * 70)
    
    try:
        schedule = load_schedule_from_json(str(selected_file))
        print(f"✓ Đã load lịch thi đấu: {len(schedule.matches)} trận")
        
        data_loader = DataLoader(data_dir="data/raw")
        teams = data_loader.load_teams()
        stadiums = data_loader.load_stadiums()
        
        print(f"✓ Đã load {len(teams)} đội")
        print(f"✓ Đã load {len(stadiums)} sân")
        
    except Exception as e:
        print(f"✗ Lỗi khi load dữ liệu: {e}")
        return
    
    # 3. Export
    print("\n[3/3] EXPORT RA EXCEL")
    print("-" * 70)
    
    # Hỏi ngày bắt đầu
    start_date = input("Ngày bắt đầu mùa giải (YYYY-MM-DD) [2025-02-15]: ").strip() or "2025-02-15"
    
    # Tạo tên file output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"outputs/schedules/schedule_{timestamp}.xlsx"
    
    try:
        export_schedule_to_excel(schedule, teams, stadiums, output_path, start_date)
        
        print("\n" + "=" * 70)
        print("HOÀN THÀNH!")
        print("=" * 70)
        print(f"File Excel: {output_path}")
        
    except Exception as e:
        print(f"✗ Lỗi khi export: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()