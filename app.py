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

# --- Giao diện Chat ---
# Hiển thị lịch sử chat (nếu có)
if "chat_session" in st.session_state and hasattr(st.session_state.chat_session, 'history'):
    for message in st.session_state.chat_session.history:
        # ---- THÊM KIỂM TRA VÀO ĐÂY ----
        msg_role = None
        if hasattr(message, 'role') and isinstance(message.role, str):
             # Chỉ gán nếu thuộc tính 'role' tồn tại và là một chuỗi
             msg_role = message.role
        else:
            # Xử lý trường hợp không có role hoặc role không phải chuỗi
            # Bạn có thể bỏ qua tin nhắn này hoặc gán một role mặc định
            st.warning(f"Tin nhắn trong lịch sử có vai trò không hợp lệ hoặc bị thiếu. Message: {message}")
            # Tùy chọn 1: Bỏ qua tin nhắn này
            # continue
            # Tùy chọn 2: Gán một role mặc định (ví dụ: 'assistant' hoặc 'model')
            msg_role = "assistant" # Hoặc "model"

        # Chỉ hiển thị nếu có role hợp lệ
        if msg_role:
            try:
                with st.chat_message(role=msg_role):
                    # Thêm kiểm tra cho message.parts để tránh lỗi khác
                    if message.parts and hasattr(message.parts[0], 'text'):
                        st.markdown(message.parts[0].text)
                    else:
                        st.markdown("_(Nội dung không hợp lệ hoặc bị thiếu)_")
            except Exception as display_error:
                 st.error(f"Lỗi khi hiển thị tin nhắn với role '{msg_role}': {display_error}")
                 st.json(message) # In ra tin nhắn gây lỗi

# Nhận input từ người dùng
user_prompt = st.chat_input("Bạn cần hỗ trợ gì?")

if user_prompt:
    # Hiển thị tin nhắn người dùng
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Gửi prompt đến Gemini và hiển thị phản hồi
    try:
        # Đảm bảo chat_session tồn tại trước khi gửi
        if "chat_session" in st.session_state:
             with st.spinner("AI đang suy nghĩ..."):
                response = st.session_state.chat_session.send_message(user_prompt)

             # Hiển thị phản hồi từ AI (vai trò 'model' thường là mặc định)
             with st.chat_message("model"):
                  st.markdown(response.text)
        else:
            st.error("Lỗi: Phiên chat chưa được khởi tạo.")

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi giao tiếp với AI: {e}")
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
