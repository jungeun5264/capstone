"""디딤돌 v9: 친구의 HTML/CSS 원본 그대로 + 원본 test.py + GPT Luna 훈련.
같은 브라우저 탭에서 URL 쿼리 또는 Streamlit 버튼으로 페이지 전환.
"""
from __future__ import annotations
from pathlib import Path
import streamlit as st
from friend_pages import original_fragment

st.set_page_config(page_title="디딤돌 | AI 활용 역량 진단·훈련", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")
BASE=Path(__file__).resolve().parent


def go(view:str)->None:
    st.query_params["view"]=view
    st.rerun()


def internal_header()->None:
    cols=st.columns([1.55,0.70,1.02,1.35,1.03,0.84],gap='small',vertical_alignment='center')
    routes=[('🌱 디딤돌','home','brand'),('홈','home','home'),('사전진단','diagnosis','diag'),
            ('맞춤형 심화 교육','training','train'),('Prompt Coach','prompt-info','prompt'),('마이페이지','mypage-info','my')]
    current=st.query_params.get('view','home')
    for col,(label,view,key) in zip(cols,routes):
        with col:
            if st.button(label,key='nav_'+key,type='primary' if (current==view and key!='brand') else 'secondary',use_container_width=True):
                go(view)
    st.divider()


def pending(title:str,body:str)->None:
    st.title(title)
    st.info(body)
    if st.button('홈으로 돌아가기',use_container_width=True):go('home')


view=st.query_params.get('view','home')
if view in ('home','diagnosis'):
    # Exactly the friend's original HTML/CSS. Page links are rewritten solely
    # in the rendered string to remain in the current tab and route to Python.
    name='index.html' if view=='home' else 'diagnosis.html'
    st.html(original_fragment(name))
else:
    st.markdown('<style>'+(BASE/'ui.css').read_text(encoding='utf-8')+'\n'+(BASE/'training.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)
    internal_header()
    if view=='diagnosis-live':
        import test
        test.render()
    elif view=='training':
        import training
        training.render_training()
    elif view=='prompt-info':
        pending('Prompt Coach','별도의 Prompt Coach 소스 코드가 아직 없어 현재는 사전진단과 실전 훈련을 제공합니다.')
    elif view=='mypage-info':
        pending('로그인·마이페이지 준비 중','사용자별 로그인 및 영구 기록 저장은 다음 구현 단계입니다.')
    else:
        go('home')
