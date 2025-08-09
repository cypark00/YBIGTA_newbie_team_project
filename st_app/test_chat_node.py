"""
Chat Node 테스트용 간단한 스크립트
실제 환경에서 UPSTAGE_API_KEY 설정 후 테스트 가능
"""
import os
from st_app.utils.state import create_initial_state, add_message
from st_app.graph.nodes.chat_node import chat_node

def test_chat_node():
    """Chat Node 기본 동작 테스트 (개선된 버전)"""
    # API 키 확인
    if not os.getenv("UPSTAGE_API_KEY"):
        print("UPSTAGE_API_KEY 환경변수가 설정되지 않았습니다.")
        print("테스트를 위해 환경변수를 설정해주세요.")
        print("\nExample:")
        print("export UPSTAGE_API_KEY='your-api-key-here'")
        return
    
    # 초기 상태 생성
    state = create_initial_state()
    
    # 테스트 시나리오들 (다양한 의도 포함)
    test_scenarios = [
        ("안녕하세요!", "chat"),
        ("롯데월드에 대해 알고 싶어요", "chat"),
        ("롯데월드 티켓 가격이 궁금해요", "subject_info"),
        ("롯데월드 운영시간을 알려주세요", "subject_info"),
        ("롯데월드 후기를 알려주세요", "review_rag"),
        ("롯데월드 어떤 놀이기구가 재미있나요?", "review_rag"),
        ("롯데월드 대기시간은 어때요?", "review_rag"),
        ("좋은 하루 되세요!", "chat")
    ]
    
    print("=== 개선된 Chat Node 테스트 시작 ===\n")
    
    for i, (user_message, expected_intent) in enumerate(test_scenarios, 1):
        print(f"테스트 {i}: {user_message}")
        print(f"   예상 의도: {expected_intent}")
        
        # 사용자 메시지 추가
        add_message(state, "user", user_message)
        
        # Chat Node 실행
        state = chat_node(state)
        
        # 결과 출력
        last_message = state["messages"][-1]
        actual_intent = state.get("intent_hint", "unknown")
        target = state.get("target", "unknown")
        
        print(f"응답: {last_message['content']}")
        print(f"분류된 의도: {actual_intent}")
        print(f"대상: {target}")
        
        # 의도 분류 정확성 체크
        intent_match = "OK" if actual_intent == expected_intent else "FAIL"
        print(f"{intent_match} 의도 분류: {actual_intent} (예상: {expected_intent})")
        
        # 응답 길이 체크 (2문장 이내)
        sentence_count = len([s for s in last_message['content'].replace('!', '.').replace('?', '.').split('.') if s.strip()])
        length_ok = "OK" if sentence_count <= 2 else "FAIL"
        print(f"{length_ok} 응답 길이: {sentence_count}문장")
        
        print("-" * 60)

def test_error_handling():
    """에러 처리 테스트"""
    print("\n=== 에러 처리 테스트 ===")
    
    # API 키 없이 테스트
    original_key = os.environ.get("UPSTAGE_API_KEY")
    if original_key:
        del os.environ["UPSTAGE_API_KEY"]
    
    state = create_initial_state()
    add_message(state, "user", "안녕하세요!")
    
    state = chat_node(state)
    
    print(f"에러 응답: {state['messages'][-1]['content']}")
    print(f"에러 정보: {state.get('error', 'None')}")
    
    # API 키 복구
    if original_key:
        os.environ["UPSTAGE_API_KEY"] = original_key

if __name__ == "__main__":
    test_chat_node()
    test_error_handling()