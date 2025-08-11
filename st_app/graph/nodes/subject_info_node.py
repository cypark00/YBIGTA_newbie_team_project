import json
import re
from typing import Dict, Any, List, Optional
from st_app.utils.state import State
from st_app.rag.llm import get_upstage_llm
import os
from st_app.rag.prompt import get_subject_info_prompt

class SubjectInfoProcessor:
    """리뷰 대상 정보 처리를 위한 클래스"""
    
    def __init__(self):
        self.subject_data = self.load_subject_data()
    
    def load_subject_data(self) -> List[Dict]:
        """subjects.json 파일 로드"""
        try:
            # 현재 파일의 위치를 기준으로 상대 경로 계산
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, "..", "..", "db", "subject_information", "subjects.json")
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # JSON이 단일 객체인 경우 리스트로 변환
                    return [data] if isinstance(data, dict) else data
            else:
                print(f"Warning: {file_path} 파일을 찾을 수 없습니다.")
                return []
        except Exception as e:
            print(f"Error loading subject data: {e}")
            return []
    
    def find_subject_by_name(self, subject_name: str) -> Optional[Dict]:
        """이름으로 주제 정보 검색"""
        subject_name_lower = subject_name.lower()
        
        for subject in self.subject_data:
            # 정확한 이름 매칭
            if subject['name'].lower() == subject_name_lower:
                return subject
            
            # 부분 매칭 (이름이 포함되어 있는 경우)
            if subject_name_lower in subject['name'].lower() or subject['name'].lower() in subject_name_lower:
                return subject
        
        return None
    
    def find_subject_by_category(self, category: str) -> List[Dict]:
        """카테고리로 주제 정보 검색"""
        return [subject for subject in self.subject_data if subject['category'] == category]
    
    def detect_category_and_subject(self, user_input: str) -> tuple[str, Optional[Dict]]:
        """사용자 입력에서 카테고리와 주제 감지"""
        user_input_lower = user_input.lower()
        
        # 1. 먼저 JSON 데이터에서 직접 이름 검색
        subject_names = [subject['name'] for subject in self.subject_data]
        for name in subject_names:
            if name.lower() in user_input_lower or any(word in user_input_lower for word in name.lower().split()):
                found_subject = self.find_subject_by_name(name)
                return found_subject['category'] if found_subject else "general", found_subject
        
        # 2. 카테고리별 키워드 검색
        category_keywords = {
            "테마파크": ["테마파크", "놀이공원", "롯데월드", "어트랙션", "놀이기구", "어드벤처", "매직아일랜드"],
            "관광지": ["관광지", "여행지", "명소"],
            "레스토랑": ["레스토랑", "맛집", "음식점"],
            "호텔": ["호텔", "숙박", "리조트"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword.lower() in user_input_lower for keyword in keywords):
                subjects = self.find_subject_by_category(category)
                return category, subjects[0] if subjects else None
        
        return "general", None
    
    def extract_subject_name(self, user_input: str) -> str:
        """사용자 입력에서 주제명 추출"""
        patterns = [
            r'(.+?)에 대해',
            r'(.+?)에 대한',
            r'(.+?) 정보',
            r'(.+?) 알려',
            r'(.+?)는',
            r'(.+?)이',
            r'(.+?) 설명',
            r'(.+?) 소개'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match:
                return match.group(1).strip()
        
        # 패턴이 매치되지 않으면 불용어 제거
        stopwords = ['에', '대해', '대한', '정보', '알려', '설명', '소개', '무엇', '어떤', '줘', '주세요']
        words = user_input.split()
        filtered_words = [word for word in words if not any(stop in word for stop in stopwords)]
        
        return ' '.join(filtered_words) if filtered_words else user_input

def format_subject_info(subject_data: Dict) -> str:
    """주제 데이터를 포맷된 문자열로 변환 - 새로운 JSON 구조 반영"""
    
    info_parts = []
    
    # 기본 정보
    info_parts.append(f"## 📍 {subject_data['name']}")
    info_parts.append(f"**카테고리**: {subject_data['category']}")
    
    if 'location' in subject_data:
        info_parts.append(f"**위치**: {subject_data['location']}")
    
    # 교통편 정보
    if 'transportation' in subject_data:
        info_parts.append(f"\n**교통편**")
        transport = subject_data['transportation']
        if 'subway' in transport:
            info_parts.append(f"🚇 **지하철**: {transport['subway']}")
        if 'bus' in transport:
            info_parts.append(f"🚌 **버스**: {transport['bus']}")
        if 'parking' in transport:
            info_parts.append(f"🅿️ **주차**: {transport['parking']}")
    
    # 설명
    if 'description' in subject_data:
        info_parts.append(f"\n**소개**\n{subject_data['description']}")
    
    # 개장일
    if 'opening_date' in subject_data:
        info_parts.append(f"\n**개장일**: {subject_data['opening_date']}")
    
    # 운영시간
    if 'opening_hours' in subject_data:
        info_parts.append(f"\n**운영시간**\n{subject_data['opening_hours']}")
    
    # 휴무일
    if 'closed_days' in subject_data:
        info_parts.append(f"\n**휴무일**: {subject_data['closed_days']}")
    
    # 티켓 정보
    if 'ticket_info' in subject_data:
        info_parts.append(f"\n**티켓 정보**")
        ticket_info = subject_data['ticket_info']
        for ticket_type, prices in ticket_info.items():
            if isinstance(prices, dict):
                price_list = []
                for age_group, price in prices.items():
                    if age_group == 'adult':
                        price_list.append(f"성인: {price}")
                    elif age_group == 'teen':
                        price_list.append(f"청소년: {price}")
                    elif age_group == 'child':
                        price_list.append(f"어린이: {price}")
                info_parts.append(f"  🎫 **{ticket_type}**: {', '.join(price_list)}")
            elif isinstance(prices, str):
                info_parts.append(f"  💰 **{ticket_type}**: {prices}")
    
    # 어트랙션 정보
    if 'attractions' in subject_data and subject_data['attractions']:
        info_parts.append(f"\n**주요 어트랙션**")
        
        attractions = subject_data['attractions']
        for area_name, area_info in attractions.items():
            info_parts.append(f"\n🎢 **{area_name}**")
            
            if isinstance(area_info, dict):
                for sub_area, attractions_list in area_info.items():
                    if isinstance(attractions_list, list):
                        info_parts.append(f"  • **{sub_area}**: {', '.join(attractions_list)}")
            elif isinstance(area_info, list):
                info_parts.append(f"  • {', '.join(area_info)}")
    
    # 시설 정보
    if 'facilities' in subject_data and subject_data['facilities']:
        info_parts.append(f"\n**시설 안내**")
        
        facilities = subject_data['facilities']
        for facility_type, facility_list in facilities.items():
            if isinstance(facility_list, list):
                info_parts.append(f"  🏢 **{facility_type}**: {', '.join(facility_list)}")
    
    # 방문 팁
    if 'visitor_tips' in subject_data and subject_data['visitor_tips']:
        info_parts.append(f"\n**방문 팁**")
        for tip in subject_data['visitor_tips']:
            info_parts.append(f"  💡 {tip}")
    
    # 웹사이트
    if 'official_website' in subject_data:
        info_parts.append(f"\n**공식 웹사이트**\n{subject_data['official_website']}")
    
    return "\n".join(info_parts)

def subject_info_node(state: State) -> State:
    """JSON 데이터를 활용한 리뷰 대상 정보 제공 노드"""
    
    processor = SubjectInfoProcessor()
    user_input = state['user_input']
    
    # 카테고리와 주제 감지
    category, found_subject = processor.detect_category_and_subject(user_input)
    extracted_subject = processor.extract_subject_name(user_input)
    
    try:
        if found_subject:
            # JSON 데이터에서 찾은 정보가 있는 경우
            formatted_info = format_subject_info(found_subject)
            
            # prompt.py의 프롬프트 사용
            llm = get_upstage_llm(temperature=0.2)
            system_prompt = get_subject_info_prompt()
            user_prompt = f"""
다음은 '{found_subject['name']}'에 대한 정보입니다:

{formatted_info}

사용자 질문: {user_input}
"""
            
            # 시스템 프롬프트와 사용자 프롬프트를 결합
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            result = llm.invoke(full_prompt)
            
            response = {
                **state,
                "result": result.content,
                "current_node": "subject_info",
                "detected_category": category,
                "extracted_subject": extracted_subject,
                "found_subject_name": found_subject['name'],
                "info_type": "subject_information",
                "data_source": "json_database"
            }
            
        else:
            # JSON 데이터에서 찾지 못한 경우 일반적인 정보 제공
            llm = get_upstage_llm(temperature=0.2)
            system_prompt = get_subject_info_prompt()
            user_prompt = f"""
'{extracted_subject}'에 대한 정보를 요청받았지만, 저희 데이터베이스에서 해당 정보를 찾을 수 없습니다.

사용자 요청: {user_input}

현재 제공 가능한 정보는 롯데월드에 대한 기본 정보입니다.
"""
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            result = llm.invoke(full_prompt)
            
            response = {
                **state,
                "result": result.content,
                "current_node": "subject_info",
                "detected_category": category,
                "extracted_subject": extracted_subject,
                "found_subject_name": None,
                "info_type": "general_information",
                "data_source": "llm_general"
            }
        
        return response
        
    except Exception as e:
        # 오류 처리
        error_response = {
            **state,
            "result": f"죄송합니다. {extracted_subject}에 대한 정보를 가져오는 중 오류가 발생했습니다. 다시 시도해 주세요.",
            "current_node": "subject_info",
            "error": str(e),
            "detected_category": category,
            "extracted_subject": extracted_subject
        }
        return error_response