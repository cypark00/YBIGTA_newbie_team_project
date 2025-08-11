import json, os, re
from typing import Dict, Any, List, Optional, Tuple
from st_app.utils.state import AppState, add_message
from st_app.rag.llm import get_upstage_llm

def _subjects_path() -> str:
    # st_app/graph/nodes/subject_info_node.py 기준 상대경로
    base = os.path.dirname(__file__)
    return os.path.normpath(os.path.join(base, "..", "..", "db", "subject_information", "subjects.json"))

def _load_subjects() -> List[Dict[str, Any]]:
    p = _subjects_path()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]

def subject_info_node(state: AppState) -> dict:
    user_input = (state.get("user_input") or "").strip()
    data = _load_subjects()
    # 여기서는 간단히 첫 항목만 사용(= 롯데월드)
    subj = data[0] if data else {}

    msgs = list(state.get("messages", []))

    try:
        llm = get_upstage_llm()
        prompt = (
            "아래 사실 정보를 기반으로 사용자의 질문에 자연스럽게 한국어로 답하세요. "
            "추측 금지.\n\n"
            f"{json.dumps(subj, ensure_ascii=False, indent=2)}\n\n"
            f"사용자 질문: {user_input}"
        )
        ans = llm.invoke(prompt).content.strip()
    except Exception:
        loc = subj.get("location","서울 송파구")
        hours = subj.get("opening_hours","공식 사이트 참고")
        ans = f"롯데월드는 {loc}에 있고 운영시간은 {hours}예요. 더 어떤 정보가 필요하신가요?"

    msgs.append({"role":"assistant","content":ans})
    return {
        "messages": msgs,
        "current_node": "subject_info",
        "error": None,
        "user_input": ""
    }