import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv # Để đọc file .env khi chạy local

# --- Kiểm tra phiên bản Streamlit lúc chạy (Để debug nếu cần) ---
# st.write(f"DEBUG: Streamlit Version at Runtime: {st.__version__}")

# --- Cấu hình cơ bản ---
st.set_page_config(page_title="AI Đồng Hành Học Đường", page_icon="🤖")
st.title("🤖 AI Đồng Hành Học Đường")
st.caption("Trò chuyện với AI để được hỗ trợ về học tập, hướng nghiệp và hơn thế nữa!")

# --- Quản lý API Key ---
# Ưu tiên 1: Lấy key từ Streamlit Secrets (khi deploy)
api_key_streamlit = st.secrets.get("GOOGLE_API_KEY")

# Ưu tiên 2: Lấy key từ file .env (khi chạy local) - Cần cài python-dotenv
load_dotenv() # Tải biến môi trường từ .env (nếu có)
api_key_env = os.getenv("GOOGLE_API_KEY")

# Chọn API Key để sử dụng
GOOGLE_API_KEY = None
if api_key_streamlit:
    GOOGLE_API_KEY = api_key_streamlit
    # st.sidebar.success("Đã tải API Key từ Streamlit Secrets.", icon="✅") # Có thể bỏ comment nếu muốn debug
elif api_key_env:
    GOOGLE_API_KEY = api_key_env
    # st.sidebar.info("Đã tải API Key từ file .env (local).", icon="📄") # Có thể bỏ comment nếu muốn debug

# Dừng nếu không có API key
if not GOOGLE_API_KEY:
    st.error("Vui lòng cấu hình Google API Key trong Streamlit Secrets hoặc file .env!")
    st.stop()

# --- Khởi tạo mô hình Gemini ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(
        'gemini-1.5-flash-latest' # Hoặc 'gemini-pro', 'gemini-1.5-pro-latest' tùy nhu cầu
    )
    # Khởi tạo chat session trong session_state nếu chưa có
    if "chat_session" not in st.session_state:
         st.session_state.chat_session = model.start_chat(history=[])
         # st.success("DEBUG: Khởi tạo chat session mới.") # Debug log

except Exception as e:
    st.error(f"Lỗi khởi tạo mô hình Gemini hoặc cấu hình API Key: {e}")
    st.stop()

# --- Giao diện Chat ---
# Hiển thị lịch sử chat (nếu có)
# Thêm kiểm tra sự tồn tại của session và history
if "chat_session" in st.session_state and hasattr(st.session_state.chat_session, 'history'):
    for message in st.session_state.chat_session.history:
        msg_role = None # Biến tạm để lưu vai trò hợp lệ
        # Kiểm tra xem message có thuộc tính 'role' và nó có phải là string không
        if hasattr(message, 'role') and isinstance(message.role, str):
            msg_role = message.role
            # Chuẩn hóa 'model' thành 'assistant' nếu cần cho st.chat_message
            if msg_role == 'model':
                msg_role = 'assistant'
        else:
            # Xử lý trường hợp thiếu role hoặc role không hợp lệ
            st.warning(f"Tin nhắn trong lịch sử có vai trò không hợp lệ hoặc bị thiếu.")
            # Gán vai trò mặc định để thử hiển thị
            msg_role = "assistant" # Hoặc có thể bỏ qua bằng 'continue'

        # Chỉ hiển thị nếu có role hợp lệ (user hoặc assistant)
        if msg_role in ["user", "assistant"]:
            try:
                # **SỬA LỖI QUAN TRỌNG: Dùng name= thay vì role=**
                with st.chat_message(name=msg_role):
                    # Kiểm tra message.parts và text trước khi truy cập
                    if message.parts and hasattr(message.parts[0], 'text'):
                        st.markdown(message.parts[0].text)
                    else:
                        st.markdown("_(Nội dung tin nhắn không hợp lệ hoặc bị thiếu)_")
            except Exception as display_error:
                 # Thông báo lỗi chi tiết hơn
                 st.error(f"Lỗi khi hiển thị tin nhắn với name '{msg_role}': {display_error}")
                 # In ra đối tượng message để debug (có thể dùng st.write)
                 st.write(f"DEBUG: Message object gây lỗi hiển thị:", message)
        else:
            # Ghi log nếu gặp role không xử lý được
            st.warning(f"Bỏ qua tin nhắn với vai trò không xác định: {msg_role}")


# Nhận input từ người dùng
user_prompt = st.chat_input("Bạn cần hỗ trợ gì?")

if user_prompt:
    # Hiển thị tin nhắn người dùng
    # **Sửa (tùy chọn nhưng nên làm): dùng name=**
    with st.chat_message(name="user"):
        st.markdown(user_prompt)

    # Gửi prompt đến Gemini và hiển thị phản hồi
    try:
        # Đảm bảo chat_session tồn tại
        if "chat_session" in st.session_state:
            with st.spinner("AI đang suy nghĩ..."):
                response = st.session_state.chat_session.send_message(user_prompt)

            # Hiển thị phản hồi từ AI
            # **Sửa (tùy chọn nhưng nên làm): dùng name=, vai trò là 'assistant'**
            with st.chat_message(name="assistant"): # Gemini trả về vai trò 'model', nhưng st.chat_message dùng 'assistant'
                 st.markdown(response.text)
        else:
            st.error("Lỗi: Phiên chat chưa được khởi tạo. Vui lòng tải lại trang.")

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi giao tiếp với AI Gemini: {e}")

# --- (Tùy chọn) Các tính năng khác ở Sidebar ---
st.sidebar.header("Thông tin thêm")
st.sidebar.write("Đây là hệ thống AI Đồng Hành Học Đường phiên bản thử nghiệm.")
# Bạn có thể thêm các thông tin khác, liên kết, hướng dẫn tại đây
