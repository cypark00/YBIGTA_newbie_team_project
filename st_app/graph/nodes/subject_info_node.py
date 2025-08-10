import json
import re
from typing import Dict, Any, List, Optional
from streamlit_app import State, llm
import os

class SubjectInfoProcessor:
    """리뷰 대상 정보 처리를 위한 클래스"""
    
    def __init__(self):
        self.subject_data = self.load_subject_data()
    
    def load_subject_data(self) -> List[Dict]:
        """subject.json 파일 로드"""
        try:
            file_path = "../subject_information/subject.json"
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
            "테마파크": ["테마파크", "놀이공원", "롯데월드", "어트랙션", "놀이기구"],
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
    """주제 데이터를 포맷된 문자열로 변환 - 업데이트된 JSON 구조 반영"""
    
    info_parts = []
    
    # 기본 정보
    info_parts.append(f"## 📍 {subject_data['name']}")
    info_parts.append(f"**카테고리**: {subject_data['category']}")
    
    if 'location' in subject_data:
        info_parts.append(f"**위치**: {subject_data['location']}")
    
    # 설명
    if 'description' in subject_data:
        info_parts.append(f"\n**소개**\n{subject_data['description']}")
    
    # 개장일
    if 'opening_date' in subject_data:
        info_parts.append(f"\n**개장일**: {subject_data['opening_date']}")
    
    # 운영시간
    if 'opening_hours' in subject_data:
        info_parts.append(f"\n**운영시간**\n{subject_data['opening_hours']}")
    
    # 어트랙션 정보 (새로운 구조 반영)
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
    
    # 시설 정보 (새로운 구조 반영)
    if 'facilities' in subject_data and subject_data['facilities']:
        info_parts.append(f"\n**시설 안내**")
        
        facilities = subject_data['facilities']
        for facility_type, facility_list in facilities.items():
            if isinstance(facility_list, list):
                info_parts.append(f"  🏢 **{facility_type}**: {', '.join(facility_list)}")
    
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
            
            # LLM을 사용해 더 자연스러운 응답 생성
            prompt = f"""
다음은 '{found_subject['name']}'에 대한 정보입니다:

{formatted_info}

위 정보를 바탕으로 사용자의 질문에 친근하고 자연스럽게 답변해 주세요.
사용자 질문: {user_input}

답변 시 다음 사항을 고려해 주세요:
1. 제공된 정보를 모두 포함하되, 자연스러운 문체로 작성
2. 사용자가 관심있어 할 만한 포인트를 강조 (특히 인기 어트랙션이나 특별한 시설)
3. 실용적인 정보(위치, 시간, 주요 시설 등)를 명확히 전달
4. 실내/실외 구분과 각 구역의 특색을 잘 설명
5. 추가로 궁금한 점이 있다면 언제든 물어보라고 안내

정확한 정보만 사용하고, 추측이나 없는 정보는 추가하지 마세요.
"""
            
            result = llm.invoke(prompt)
            
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
            prompt = f"""
'{extracted_subject}'에 대한 정보를 요청받았지만, 저희 데이터베이스에서 해당 정보를 찾을 수 없습니다.

사용자 요청: {user_input}

다음과 같이 응답해 주세요:
1. 현재 데이터베이스에 해당 정보가 없음을 정중히 안내
2. 현재 제공 가능한 정보 카테고리 안내 (예: 테마파크, 관광지 등)
3. 다른 관련 정보로 도움을 드릴 수 있는지 제안
4. 일반적인 정보라도 도움이 될만한 내용이 있다면 간략히 제공

친근하고 도움이 되는 톤으로 답변해 주세요.
"""
            
            result = llm.invoke(prompt)
            
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