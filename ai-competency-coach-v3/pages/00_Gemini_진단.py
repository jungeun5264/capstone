import os
import streamlit as st
from google import genai

st.set_page_config(page_title="Gemini 연결 진단", page_icon="🧪")

for key in ("GEMINI_API_KEY","GEMINI_MODEL"):
    try:
        if key in st.secrets and st.secrets[key]:
            os.environ[key]=str(st.secrets[key])
    except Exception:
        pass

api_key=os.getenv("GEMINI_API_KEY")
model=os.getenv("GEMINI_MODEL")

st.title("🧪 Gemini 연결 진단")
st.caption("평가기준이나 rubric 없이 아주 짧은 요청만 보내는 테스트입니다.")

if not api_key:
    st.error("GEMINI_API_KEY가 없습니다.")
    st.stop()
if not model:
    st.error("GEMINI_MODEL이 없습니다.")
    st.stop()

st.write(f"현재 설정 모델: `{model}`")
client=genai.Client(api_key=api_key)

def ping(m):
    return client.models.generate_content(
        model=m,
        contents='연결 테스트입니다. 반드시 "OK" 두 글자만 답해주세요.'
    )

if st.button("① 현재 모델만 테스트", use_container_width=True):
    try:
        r=ping(model)
        st.success("현재 모델 연결 성공")
        st.code(r.text or "(빈 응답)")
    except Exception as e:
        st.error("현재 모델 연결 실패")
        st.code(f"{type(e).__name__}: {e}")

st.divider()

if st.button("② Gemini 3.5 Flash-Lite 테스트", use_container_width=True):
    try:
        r=ping("gemini-3.5-flash-lite")
        st.success("Gemini 3.5 Flash-Lite 연결 성공")
        st.code(r.text or "(빈 응답)")
    except Exception as e:
        st.error("Gemini 3.5 Flash-Lite 연결 실패")
        st.code(f"{type(e).__name__}: {e}")

st.markdown("""
### 결과 해석
- **① 성공** → API Key와 현재 모델 연결은 정상. 기존 역량진단 요청 구조를 줄이면 됩니다.
- **① 실패 + ② 성공** → 현재 모델 쪽 문제일 가능성이 큽니다.
- **①, ② 둘 다 실패** → 프롬프트 문제가 아니라 API Key/프로젝트/계정 쪽 설정을 확인해야 합니다.
""")
