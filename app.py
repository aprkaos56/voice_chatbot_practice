import streamlit as st
import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
from io import BytesIO

# 환경 변수 로드
load_dotenv()
client = OpenAI()

# 페이지 설정
st.set_page_config(page_title="국내 관광지 추천기", page_icon="🚞")

# 제목
st.title("🚞 국내 관광지 추천기 🏄")
st.write("음성이나 텍스트로 여행 조건을 입력하면 국내 관광지 3곳을 추천해줍니다.")

# 세션 상태 초기화
if "texts" not in st.session_state:
    st.session_state.texts = []

if "needs" not in st.session_state:
    st.session_state.needs = ""

if "answer" not in st.session_state:
    st.session_state.answer = ""


# 음성 인식 함수
def recognize_once():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        st.info("🎤 말씀해주세요...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)

    text = recognizer.recognize_google(audio, language="ko-KR")
    return text


# 추천 생성 함수
def make_recommendation(needs):
    prompt = f"""
사용자 여행 조건: {needs}

이 조건에 맞는 국내 여행지 3곳을 추천해줘.
각 추천지는 추천 이유를 두 가지씩 설명해줘.
또 각 장소의 평점을 10점 만점으로 말해줘.

주의사항:
- Markdown 기호는 쓰지 마
- 자연스럽게 읽히는 문장으로 작성해줘

형식:
추천 여행지 세 곳을 안내해드릴게요.

첫 번째 추천지는 [장소명]입니다.
추천 이유 첫 번째, [이유]
추천 이유 두 번째, [이유]
평점은 10점 만점에 [점수]점입니다.

두 번째 추천지는 [장소명]입니다.
추천 이유 첫 번째, [이유]
추천 이유 두 번째, [이유]
평점은 10점 만점에 [점수]점입니다.

세 번째 추천지는 [장소명]입니다.
추천 이유 첫 번째, [이유]
추천 이유 두 번째, [이유]
평점은 10점 만점에 [점수]점입니다.

마지막에는 전체 내용을 짧게 정리해줘.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text


# TTS 함수
def make_tts_audio(text):
    mp3_buffer = BytesIO()
    tts = gTTS(text=text, lang="ko")
    tts.write_to_fp(mp3_buffer)
    mp3_buffer.seek(0)
    return mp3_buffer


# 1. 조건 입력
st.subheader("🧳 1. 여행 조건 입력")

if st.button("🎤 음성으로 입력"):
    try:
        heard = recognize_once()
        st.session_state.texts.append(heard)
        st.success(f"인식 결과: {heard}")
    except sr.WaitTimeoutError:
        st.error("말하는 시간을 감지하지 못했습니다.")
    except sr.UnknownValueError:
        st.error("음성을 인식하지 못했습니다.")
    except sr.RequestError:
        st.error("음성 인식 서비스 오류가 발생했습니다.")
    except Exception as e:
        st.error(f"오류 발생: {e}")

manual_input = st.text_input("✏️ 직접 조건 입력", placeholder="예: 바다가 보이고 조용한 곳")

col1, col2 = st.columns(2)

with col1:
    if st.button("➕ 조건 추가"):
        if manual_input.strip():
            st.session_state.texts.append(manual_input.strip())
            st.success("조건이 추가되었습니다.")
        else:
            st.warning("조건을 입력해주세요.")

with col2:
    if st.button("🧹 초기화"):
        st.session_state.texts = []
        st.session_state.needs = ""
        st.session_state.answer = ""
        st.success("초기화되었습니다.")

st.write("현재 입력된 조건")
if st.session_state.texts:
    for i, text in enumerate(st.session_state.texts, start=1):
        st.write(f"{i}. {text}")
else:
    st.write("입력된 조건이 없습니다.")


# 2. 조건 정리
st.subheader("📌 2. 조건 정리")

if st.button("📍 조건 합치기"):
    st.session_state.needs = " ".join(st.session_state.texts)

st.text_area("정리된 조건", st.session_state.needs, height=100)


# 3. 추천 결과 생성
st.subheader("🗺️ 3. 관광지 추천")

if st.button("🚞 추천 받기"):
    if not st.session_state.texts:
        st.warning("먼저 조건을 입력해주세요.")
    else:
        st.session_state.needs = " ".join(st.session_state.texts)
        with st.spinner("추천 결과 생성 중..."):
            try:
                st.session_state.answer = make_recommendation(st.session_state.needs)
                st.success("추천이 완료되었습니다.")
            except Exception as e:
                st.error(f"오류 발생: {e}")

st.text_area("추천 결과", st.session_state.answer, height=350)


# 4. 음성 출력
st.subheader("🔊 4. 음성으로 듣기")

if st.button("🎧 음성 재생"):
    if not st.session_state.answer:
        st.warning("먼저 추천 결과를 생성해주세요.")
    else:
        try:
            audio_buffer = make_tts_audio(st.session_state.answer)
            st.audio(audio_buffer, format="audio/mp3")
        except Exception as e:
            st.error(f"음성 변환 오류: {e}")