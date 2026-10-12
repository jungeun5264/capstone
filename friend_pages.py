"""원본 Figma HTML/CSS 파일의 내용을 수정하지 않고 Streamlit에서 렌더링합니다.
브라우저가 새 탭을 만들지 않게 하는 링크 변환은 메모리 안에서만 일어납니다.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

def original_fragment(name: str) -> str:
    """Return original page BODY rendered with original CSS; route links only in memory."""
    assert name in ('index.html','diagnosis.html')
    raw=(ROOT/name).read_text(encoding='utf-8')
    match=re.search(r'<body[^>]*>(.*?)</body>', raw, re.IGNORECASE|re.DOTALL)
    if not match: raise ValueError(f'{name}: body 요소를 찾을 수 없습니다.')
    body=match.group(1)
    # Only href values are adapted. No source HTML/CSS is rewritten on disk.
    for original, target in [('index.html','home'), ('diagnosis.html','diagnosis')]:
        body=body.replace(f'href="{original}"', f'href="?view={target}" target="_self"')
    links = {
        '맞춤형 심화 교육': 'training',
        'Prompt Coach': 'prompt-info',
        '마이페이지': 'mypage-info',
    }
    for label, route in links.items():
        body=body.replace(f'<a href="#">{label}</a>', f'<a href="?view={route}" target="_self">{label}</a>')
    body=body.replace('<a href="#" class="btn-white">회원가입하기</a>',
                      '<a href="?view=mypage-info" target="_self" class="btn-white">회원가입하기</a>')
    body=body.replace('<a href="#" class="btn-start">',
                      '<a href="?view=diagnosis-live" target="_self" class="btn-start">')
    # Keep the friend's file as-is; correct only the outdated text of the displayed
    # preview to match the user's actual test.py (7 scenarios, 6 assessed areas).
    if name=='diagnosis.html':
        body=body.replace('소요 시간: 약 3~5분 (총 12문항 / 영역별 4문항)',
                          '소요 시간: 약 5~8분 (총 7개 상황 / 6개 역량)')
        body=body.replace('진단 완료 시 개인별 맞춤 추천 코스와<br>Prompt Coach 실습이 즉시 활성화됩니다.',
                          '진단 완료 시 6개 역량 분석과<br>실전 훈련으로 이동할 수 있습니다.')
    css=(ROOT/'style.css').read_text(encoding='utf-8')
    if name=='diagnosis.html': css += '\n'+(ROOT/'diagnosis.css').read_text(encoding='utf-8')
    # Original CSS applies directly; page-shell styles only neutralize Streamlit's
    # default centered/padded app container. The 4 original files remain intact.
    shim = """
    [data-testid='stMainBlockContainer'], .block-container{
      max-width:100%!important;width:100%!important;padding:0!important;
    }
    [data-testid='stAppViewContainer'],.stApp{background:#fff!important;}
    [data-testid='stHeader']{display:none!important;}
    #MainMenu,footer{visibility:hidden!important;}
    [data-testid='stVerticalBlock']{gap:0!important;}
    [data-testid='stElementContainer']{width:100%;}
    """
    return "<style>@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');\n" + css + '\n' + shim + '</style>\n' + body
