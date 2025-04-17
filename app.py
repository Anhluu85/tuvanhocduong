import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv # Để đọc file .env khi chạy local

# --- Cấu hình cơ bản ---
st.set_page_config(page_title="AI Đồng Hành Học Đường", page_icon="🤖")
st.title("🤖 AI Đồng Hành Học Đường")
st.caption("Trò chuyện với AI để được hỗ trợ về học tập, hướng nghiệp và hơn thế nữa!")

# --- Quản lý API Key ---
# Ưu tiên 1: Lấy key từ Streamlit Secrets (khi deploy)
api_key_streamlit = st.secrets.get("GOOGLE_API_KEY")

# Ưu tiên 2: Lấy key từ file .env (khi chạy local) - Cần cài python-dotenv
load_dotenv()
api_key_env = os.getenv("GOOGLE_API_KEY")

# Ưu tiên 3: Cho phép người dùng nhập (ít an toàn hơn, chỉ dùng để test nhanh)
# api_key_input = st.text_input("Nhập Google API Key của bạn (nếu chưa cấu hình):", type="password")

# Chọn API Key để sử dụng
if api_key_streamlit:
    GOOGLE_API_KEY = api_key_streamlit
    st.sidebar.success("Đã tải API Key từ Streamlit Secrets.", icon="✅")
elif api_key_env:
    GOOGLE_API_KEY = api_key_env
    st.sidebar.info("Đã tải API Key từ file .env (local).", icon="📄")
# elif api_key_input:
#     GOOGLE_API_KEY = api_key_input
#     st.sidebar.warning("Sử dụng API Key do người dùng nhập.", icon="⚠️")
else:
    st.error("Vui lòng cấu hình Google API Key trong Streamlit Secrets hoặc file .env!")
    st.stop() # Dừng ứng dụng nếu không có key

# --- Khởi tạo mô hình Gemini ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(
        'gemini-1.5-flash-latest' # Hoặc 'gemini-pro', 'gemini-1.5-pro-latest' tùy nhu cầu
        # Cân nhắc thêm safety_settings nếu cần kiểm soát nội dung chặt chẽ hơn
        # safety_settings=[...]
    )
    # (Tùy chọn) Khởi tạo chat history nếu muốn duy trì ngữ cảnh cuộc trò chuyện
    if "chat_session" not in st.session_state:
         st.session_state.chat_session = model.start_chat(history=[])

except Exception as e:
    st.error(f"Lỗi khởi tạo mô hình Gemini: {e}")
    st.stop()

# --- Giao diện Chat ---
# Hiển thị lịch sử chat (nếu có)
for message in st.session_state.chat_session.history:
    with st.chat_message(role=message.role):
        st.markdown(message.parts[0].text)

# Nhận input từ người dùng
user_prompt = st.chat_input("Bạn cần hỗ trợ gì?")

if user_prompt:
    # Hiển thị tin nhắn người dùng
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Gửi prompt đến Gemini và hiển thị phản hồi
    try:
        with st.spinner("AI đang suy nghĩ..."): # Hiệu ứng chờ
            # Gửi prompt đến session chat hiện tại
            response = st.session_state.chat_session.send_message(user_prompt)

        # Hiển thị phản hồi từ AI
        with st.chat_message("model"): # 'model' là role mặc định của Gemini trong history
             st.markdown(response.text)

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi giao tiếp với AI: {e}")

# --- (Tùy chọn) Các tính năng khác ---
st.sidebar.header("Thông tin thêm")
st.sidebar.write("Đây là phiên bản demo của hệ thống tư vấn học đường bằng AI.")
# Bạn có thể thêm các nút, thông tin liên hệ chuyên gia, v.v... ở đây
