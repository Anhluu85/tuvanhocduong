import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv # Để đọc file .env khi chạy local
import datetime # Thêm để có timestamp

# --- Cấu hình cơ bản ---
st.set_page_config(page_title="AI Đồng Hành Học Đường", page_icon="🤖", layout="wide") # Thêm layout="wide"
st.title("🤖 AI Đồng Hành Học Đường")
st.caption("Trò chuyện với AI để được hỗ trợ về học tập, hướng nghiệp và hơn thế nữa!")

# --- Quản lý API Key ---
# (Giữ nguyên code quản lý API Key của bạn)
# Ưu tiên 1: Lấy key từ Streamlit Secrets (khi deploy)
api_key_streamlit = st.secrets.get("GOOGLE_API_KEY")
# Ưu tiên 2: Lấy key từ file .env (khi chạy local)
load_dotenv()
api_key_env = os.getenv("GOOGLE_API_KEY")
# Chọn API Key
GOOGLE_API_KEY = api_key_streamlit or api_key_env
if not GOOGLE_API_KEY:
    st.error("Vui lòng cấu hình Google API Key trong Streamlit Secrets hoặc file .env!")
    st.stop()

# --- Khởi tạo mô hình Gemini ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(
        'gemini-1.5-flash-latest' # Hoặc 'gemini-pro', 'gemini-1.5-pro-latest'
    )
    # --- QUAN TRỌNG: Quản lý lịch sử trong session_state ---
    # Chúng ta sẽ lưu lịch sử riêng để dễ dàng thêm lời chào và quản lý
    if "gemini_history" not in st.session_state:
        st.session_state.gemini_history = []
        # Chỉ khởi tạo chat session API khi cần gửi tin nhắn đầu tiên
        # Bỏ st.session_state.chat_session = model.start_chat(history=[]) ở đây

except Exception as e:
    st.error(f"Lỗi khởi tạo mô hình Gemini hoặc cấu hình API Key: {e}")
    st.stop()

# --- Hàm gửi tin nhắn và cập nhật lịch sử (bao gồm cả history của API) ---
# Cần hàm này để đồng bộ history của API và history hiển thị
def send_message_to_gemini(prompt):
    try:
        # Khởi tạo chat session API nếu chưa có hoặc nếu history API trống
        # Điều này cho phép chúng ta thêm tin nhắn hệ thống/chào mừng vào history hiển thị
        # mà không gửi nó lên API ngay lập tức.
        if "api_chat_session" not in st.session_state:
             # Xây dựng lại history cho API từ history hiển thị (loại bỏ lời chào)
             api_history_for_init = []
             for msg in st.session_state.gemini_history:
                 # Chỉ lấy tin nhắn user/assistant thực sự, không lấy lời chào/hướng dẫn
                 if msg["role"] in ["user", "assistant"] and msg.get("is_greeting", False) is False:
                     api_history_for_init.append({
                         "role": "user" if msg["role"] == "user" else "model", # Chuyển 'assistant' thành 'model' cho API
                         "parts": [{"text": msg["content"]}]
                     })
             st.session_state.api_chat_session = model.start_chat(history=api_history_for_init)
             print("DEBUG: Initialized API chat session.")

        # Gửi tin nhắn mới
        response = st.session_state.api_chat_session.send_message(prompt)
        return response.text
    except Exception as e:
        st.error(f"Lỗi khi gửi tin nhắn đến Gemini: {e}")
        print(f"Error sending message to Gemini: {e}") # Log lỗi
        return None # Trả về None nếu lỗi

# --- Giao diện Chat ---

# 1. Hiển thị lời chào và giới thiệu ban đầu (chỉ khi lịch sử trống)
if not st.session_state.gemini_history:
    timestamp_greet = datetime.datetime.now()
    greeting_message = {
        "role": "assistant",
        "content": (
            "Xin chào! Mình là AI Đồng Hành, ở đây để lắng nghe và hỗ trợ bạn. "
            "Mình có thể cung cấp thông tin, gợi ý giải pháp cho các vấn đề học đường thường gặp. 😊\n\n"
            "**Lưu ý:** Mình chỉ là AI hỗ trợ, không thay thế chuyên gia tâm lý. "
            "Nếu bạn đang gặp khủng hoảng, hãy liên hệ ngay với người lớn tin cậy hoặc [Đường dây nóng hỗ trợ](#). <span style='color:red; font-weight:bold;'>(Cần thay link/số thật)</span>"
        ),
        "timestamp": timestamp_greet,
        "is_greeting": True # Đánh dấu đây là tin nhắn chào mừng
    }
    st.session_state.gemini_history.append(greeting_message) # Lưu vào lịch sử hiển thị
    # Tin nhắn này không được gửi lên API history ban đầu

# 2. Hiển thị các tin nhắn đã có trong lịch sử `st.session_state.gemini_history`
for message in st.session_state.gemini_history:
    role = message["role"]
    avatar = "🧑‍🎓" if role == "user" else "🤖"
    with st.chat_message(name=role, avatar=avatar): # Sử dụng name=role
        st.markdown(message["content"], unsafe_allow_html=True) # Cho phép HTML cho link/định dạng trong lời chào
        if "timestamp" in message:
             st.caption(message["timestamp"].strftime('%H:%M:%S %d/%m/%Y'))

# 3. Ô nhập liệu và xử lý input mới
user_prompt = st.chat_input("Bạn cần hỗ trợ gì?")

if user_prompt:
    # a. Lưu và Hiển thị tin nhắn người dùng
    timestamp_user = datetime.datetime.now()
    user_message = {"role": "user", "content": user_prompt, "timestamp": timestamp_user}
    st.session_state.gemini_history.append(user_message)
    with st.chat_message(name="user", avatar="🧑‍🎓"):
        st.markdown(user_prompt)
        st.caption(timestamp_user.strftime('%H:%M:%S %d/%m/%Y'))

    # b. Gửi prompt đến Gemini và nhận phản hồi
    with st.spinner("AI đang suy nghĩ..."):
        ai_response_content = send_message_to_gemini(user_prompt)

    # c. Hiển thị và Lưu tin nhắn AI (nếu có phản hồi)
    if ai_response_content:
        timestamp_ai = datetime.datetime.now()
        ai_message = {"role": "assistant", "content": ai_response_content, "timestamp": timestamp_ai}
        st.session_state.gemini_history.append(ai_message)
        with st.chat_message(name="assistant", avatar="🤖"):
            st.markdown(ai_response_content)
            st.caption(timestamp_ai.strftime('%H:%M:%S %d/%m/%Y'))
    else:
        # Có thể thêm thông báo nếu AI không trả lời được
        st.warning("AI hiện tại không thể phản hồi. Vui lòng thử lại sau.")


# --- Sidebar với các liên kết (Tích hợp từ mẫu) ---
with st.sidebar:
    st.header("Công cụ khác")
    # !!! THAY BẰNG ĐƯỜNG DẪN THỰC TẾ ĐẾN CÁC TRANG CỦA BẠN !!!
    # Ví dụ: st.page_link("pages/02_📚_Thư_viện.py", label="📚 Thư viện Tài nguyên")
    # Ví dụ: st.page_link("pages/03_📅_Đặt_lịch.py", label="📅 Đặt lịch hẹn")
    st.markdown("- [📚 Thư viện Tài nguyên](#)") # Placeholder link
    st.markdown("- [📅 Đặt lịch hẹn](#)")     # Placeholder link
    st.divider()
    st.header("Hỗ trợ khẩn cấp")
    # !!! THAY BẰNG THÔNG TIN THẬT !!!
    st.markdown("- Đường dây nóng ABC: [Số điện thoại]")
    st.markdown("- Tư vấn viên trường XYZ: [Thông tin liên hệ]")
    st.divider()
    st.info("AI Đồng Hành đang trong giai đoạn thử nghiệm.")

# --- NHẮC NHỞ QUAN TRỌNG ---
st.sidebar.warning("Lưu ý: Lịch sử chat hiện tại **chưa được lưu** vào Cơ sở dữ liệu Neon.")
