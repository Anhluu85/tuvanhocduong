# app.py

import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import datetime
import psycopg2 # Để tương tác với PostgreSQL (Neon)
import pandas as pd # Vẫn cần cho một số xử lý dữ liệu

# --- Cấu hình cơ bản ---
st.set_page_config(
    page_title="Trợ Lý Học Đường AI",
    page_icon="🤖",
    layout="wide" # Sử dụng layout rộng cho giao diện chat
)

st.title("🤖 Trợ Lý Học Đường AI")
# Sử dụng caption đã chọn
st.caption("Hỏi đáp cùng AI về học tập, nghề nghiệp, cảm xúc và các khó khăn trong đời sống học đường.")

# --- Quản lý API Key và Cấu hình ---

# Load .env file if it exists (for local development)
load_dotenv()

# Lấy Google API Key
google_api_key = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))
if not google_api_key:
    st.error("Lỗi: Không tìm thấy GOOGLE_API_KEY. Vui lòng cấu hình trong Streamlit Secrets hoặc file .env.")
    st.stop()

# Lấy thông tin kết nối DB Neon
db_secrets = st.secrets.get("database")
if not db_secrets:
    st.error("Lỗi: Không tìm thấy cấu hình [database] trong Streamlit Secrets.")
    # Không dừng hoàn toàn, nhưng chức năng cảnh báo sẽ không hoạt động
    # st.stop() # Bỏ comment nếu CSDL là bắt buộc ngay từ đầu

# --- Khởi tạo Mô hình Gemini ---
try:
    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest') # Hoặc phiên bản khác
except Exception as e:
    st.error(f"Lỗi khởi tạo mô hình Gemini: {e}")
    print(f"Gemini Initialization Error: {e}")
    st.stop()

# --- Phần Kết nối và Tương tác CSDL ---

# Sử dụng cache_resource cho kết nối DB để tái sử dụng
@st.cache_resource(ttl=600)
def connect_db():
    """Kết nối đến CSDL PostgreSQL."""
    print("Attempting to connect to the database...")
    if not db_secrets: # Kiểm tra lại nếu db_secrets chưa được load
        print("DB connection info missing in secrets.")
        return None
    try:
        if "uri" in db_secrets:
            conn = psycopg2.connect(db_secrets["uri"])
        elif "host" in db_secrets:
            conn = psycopg2.connect(
                host=db_secrets["host"],
                port=db_secrets.get("port", 5432),
                dbname=db_secrets["dbname"],
                user=db_secrets["user"],
                password=db_secrets["password"],
                sslmode=db_secrets.get("sslmode", "require")
            )
        else:
            print("DB connection info incomplete in secrets.")
            return None
        print("Database connection successful!")
        return conn
    except psycopg2.OperationalError as e:
         # Không hiển thị lỗi trực tiếp trên UI chính, chỉ log
         print(f"DB Connection OperationalError: {e}. Check credentials, host, port, network, SSL.")
         return None
    except Exception as e:
        print(f"DB Connection Error: {e}")
        return None

# Trong hàm create_alert_in_db

def create_alert_in_db(session_id, reason, snippet, priority, status='Mới', user_id_associated=None): # Vẫn nhận user_id nhưng không dùng trong INSERT
    """Tạo một bản ghi cảnh báo mới trong bảng 'alerts'."""
    conn = connect_db()
    if conn is None:
        print("Error in create_alert_in_db: No DB connection.")
        st.warning("Không thể ghi nhận cảnh báo do lỗi kết nối CSDL.")
        return False

    cursor = None
    alert_created = False
    try:
        cursor = conn.cursor()
        print(f"Creating alert: session={session_id}, reason='{reason}', priority={priority}")

        # --- SỬA LẠI DÒNG NÀY ---
        # Bỏ user_id_associated khỏi danh sách cột
        sql = """
            INSERT INTO alerts (chat_session_id, reason, snippet, priority, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        # --- VÀ SỬA LẠI DÒNG NÀY ---
        # Bỏ user_id_associated khỏi tuple giá trị
        cursor.execute(sql, (session_id, reason, snippet, priority, status))
        # --------------------------

        conn.commit()
        alert_created = True
        print(f"Alert created successfully for session {session_id}.")
    except Exception as e:
        if conn: conn.rollback()
        print(f"--- DATABASE ERROR Creating Alert ---")
        print(f"Session ID: {session_id}, Reason: {reason}")
        print(f"Error: {e}, Type: {type(e).__name__}")
        print(f"-----------------------------------")
        st.warning(f"Gặp sự cố khi lưu cảnh báo vào hệ thống ({type(e).__name__}).")
    finally:
        if cursor: cursor.close()

    return alert_created

# Lưu lịch sử
def save_message_to_db(session_id, user_id, sender, content, is_greeting=False, is_emergency=False):
    """Lưu một tin nhắn vào bảng 'conversations'."""
    conn = connect_db() # Lấy kết nối CSDL
    if conn is None:
        print("Error saving message: No DB connection.")
        # Không nên hiện lỗi trên UI chat chính, chỉ log
        return False

    cursor = None
    saved = False
    try:
        cursor = conn.cursor()
        print(f"Saving message: session={session_id}, user={user_id}, sender={sender}") # Log
        # KIỂM TRA TÊN BẢNG/CỘT CHO KHỚP CSDL CỦA BẠN
        sql = """
            INSERT INTO conversations (session_id, user_id, sender, message_content, is_greeting, is_emergency)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (session_id, user_id, sender, content, is_greeting, is_emergency))
        conn.commit() # Lưu vào CSDL
        saved = True
        print("Message saved successfully.") # Log
    except Exception as e:
        if conn: conn.rollback()
        print(f"--- DATABASE ERROR Saving Message ---")
        print(f"Session: {session_id}, User: {user_id}, Sender: {sender}")
        print(f"Error: {e}, Type: {type(e).__name__}")
        print(f"-----------------------------------")
        # Không nên hiện lỗi trên UI chat chính
    finally:
        if cursor: cursor.close()
        # Không đóng conn

    return saved
# --- Phần Logic Nhận diện Rủi ro ---

# !!! DANH SÁCH TỪ KHÓA RẤT CƠ BẢN - CẦN MỞ RỘNG VÀ XÁC THỰC !!!
RISK_KEYWORDS = {
    "tự hại": ["muốn chết", "kết thúc", "tự tử", "không muốn sống", "tự làm đau", "dao kéo", "tuyệt vọng"],
    "bạo lực": ["bị đánh", "bị đập", "bị trấn", "bị đe dọa", "bắt nạt hội đồng"],
    # Thêm các nhóm khác: lo âu nghiêm trọng, lạm dụng,...
}

def detect_risk(text):
    """Phát hiện từ khóa rủi ro. Trả về loại rủi ro hoặc None."""
    text_lower = text.lower()
    for risk_type, keywords in RISK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                print(f"!!! RISK DETECTED: Type={risk_type}, Keyword='{keyword}'")
                return risk_type
    return None

def get_emergency_response_message(risk_type):
    """Trả về nội dung tin nhắn khẩn cấp soạn sẵn."""
    # !!! THAY BẰNG THÔNG TIN LIÊN HỆ THẬT !!!
    emergency_contacts = """
- Đường dây nóng ABC: **[SỐ ĐIỆN THOẠI THẬT]**
- Tư vấn viên trường XYZ: **[THÔNG TIN LIÊN HỆ THẬT]**
- Hoặc nói chuyện ngay với thầy/cô/người lớn mà bạn tin tưởng nhất."""

    base_message = f"Mình nhận thấy bạn đang đề cập đến một vấn đề rất nghiêm trọng ({risk_type}). Sự an toàn của bạn là quan trọng nhất lúc này. " \
                   f"Mình là AI và không thể thay thế sự hỗ trợ trực tiếp từ chuyên gia. " \
                   f"Vui lòng liên hệ ngay các nguồn trợ giúp sau đây nhé:\n{emergency_contacts}"
    return base_message

# --- Quản lý Session Chat Gemini và Lịch sử Hiển thị ---

if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []
    print("Initialized empty display history.")

if "api_chat_session" not in st.session_state:
    # Chỉ khởi tạo khi cần gửi tin nhắn đầu tiên hoặc reset
    st.session_state.api_chat_session = None
    print("API Chat Session placeholder created.")

def get_api_chat_session():
    """Lấy hoặc khởi tạo session chat với Gemini API."""
    if st.session_state.api_chat_session is None:
        print("API chat session is None, attempting to initialize...")
        try:
            # Xây dựng history cho API từ history hiển thị (loại lời chào, chuyển role)
            api_history_for_init = []
            for msg in st.session_state.gemini_history:
                if msg["role"] in ["user", "assistant"] and not msg.get("is_greeting", False):
                    api_role = "user" if msg["role"] == "user" else "model"
                    api_history_for_init.append({"role": api_role, "parts": [{"text": msg["content"]}]})

            st.session_state.api_chat_session = model.start_chat(history=api_history_for_init)
            print("Initialized API chat session successfully.")
        except Exception as e:
            st.error("Lỗi khởi tạo phiên chat với AI. Vui lòng thử lại.")
            print(f"Error initializing API chat session: {e}")
            return None # Trả về None nếu không khởi tạo được
    return st.session_state.api_chat_session

# --- Giao diện Chat Chính ---

# 1. Hiển thị lời chào ban đầu
if not st.session_state.gemini_history:
    timestamp_greet = datetime.datetime.now()
    greeting_content = (
        "Xin chào! Mình là Trợ Lý Học Đường AI, ở đây để lắng nghe và hỗ trợ bạn. "
        "Hãy hỏi mình về học tập, nghề nghiệp, cảm xúc hoặc những khó khăn bạn gặp nhé! 😊\n\n"
        "**Lưu ý:** Mình chỉ là AI hỗ trợ, không thay thế chuyên gia tâm lý. "
        "Nếu bạn đang gặp khủng hoảng, hãy liên hệ ngay với người lớn tin cậy hoặc [Đường dây nóng hỗ trợ](#). <span style='color:red; font-weight:bold;'>(Cần thay link/số thật)</span>"
    )
    greeting_message = {
        "role": "assistant", "content": greeting_content,
        "timestamp": timestamp_greet, "is_greeting": True
    }
    st.session_state.gemini_history.append(greeting_message)
    print("Added initial greeting message to display history.")

# 2. Hiển thị lịch sử chat
for message in st.session_state.gemini_history:
    role = message["role"]
    avatar = "🧑‍🎓" if role == "user" else "🤖"
    with st.chat_message(name=role, avatar=avatar):
        # Cho phép HTML cho link trong lời chào, nhưng cẩn thận với input người dùng
        allow_html = message.get("is_greeting", False) or message.get("is_emergency", False)
        st.markdown(message["content"], unsafe_allow_html=allow_html)
        if "timestamp" in message:
             st.caption(message["timestamp"].strftime('%H:%M:%S %d/%m/%Y'))
        if message.get("is_emergency", False):
             st.error("❗ Hãy ưu tiên liên hệ hỗ trợ khẩn cấp theo thông tin trên.")

# 3. Ô nhập liệu và xử lý
# --- Trong khối xử lý input mới ---
user_prompt = st.chat_input("Nhập câu hỏi hoặc điều bạn muốn chia sẻ...")

if user_prompt:
    # --- QUAN TRỌNG: Xác định session_id và user_id (HIỆN TẠI LÀ TẠM THỜI) ---
    # !!! THAY BẰNG LOGIC LẤY ID THẬT SAU NÀY !!!
    temp_session_id = "temp_session_123"
    temp_user_id = "temp_user_abc"
    # ---------------------------------------------------------------------

    # a. Lưu và Hiển thị tin nhắn người dùng
    timestamp_user = datetime.datetime.now()
    user_message = {"role": "user", "content": user_prompt, "timestamp": timestamp_user}
    st.session_state.gemini_history.append(user_message)
    # *** GỌI HÀM LƯU TIN NHẮN USER ***
    save_message_to_db(
        session_id=temp_session_id,
        user_id=temp_user_id,
        sender="user",
        content=user_prompt
    )
    # Hiển thị tin nhắn user (như cũ)
    with st.chat_message(name="user", avatar="🧑‍🎓"):
        st.markdown(user_prompt)
        st.caption(timestamp_user.strftime('%H:%M:%S %d/%m/%Y'))

    # b. Xử lý prompt: Kiểm tra rủi ro trước
    ai_response_content = None
    is_emergency_response = False
    detected_risk = detect_risk(user_prompt)

    with st.spinner("Trợ lý AI đang xử lý..."):
        if detected_risk:
            # ... (logic xử lý rủi ro và tạo cảnh báo như cũ) ...
            is_emergency_response = True
            ai_response_content = get_emergency_response_message(detected_risk)
            create_alert_in_db(
                session_id=temp_session_id,
                reason=f"Phát hiện rủi ro: {detected_risk}",
                snippet=user_prompt[:500],
                priority=1,
                user_id_associated=temp_user_id # Cột này trong alerts
            )
        else:
            # ... (logic gọi Gemini như cũ) ...
             chat_session = get_api_chat_session()
             if chat_session:
                 try:
                     response = chat_session.send_message(user_prompt)
                     ai_response_content = response.text
                     print("Received response from Gemini.")
                 except Exception as e:
                     st.error(f"Đã xảy ra lỗi khi giao tiếp với AI Gemini: {e}")
                     print(f"Error calling Gemini API: {e}")
             else:
                 ai_response_content = "Xin lỗi, đã có lỗi xảy ra với phiên chat AI."

    # c. Hiển thị và Lưu tin nhắn AI (nếu có phản hồi)
    if ai_response_content:
        timestamp_ai = datetime.datetime.now()
        ai_message = {
            "role": "assistant", "content": ai_response_content,
            "timestamp": timestamp_ai, "is_emergency": is_emergency_response
        }
        st.session_state.gemini_history.append(ai_message)
        # *** GỌI HÀM LƯU TIN NHẮN AI ***
        save_message_to_db(
            session_id=temp_session_id,
            user_id=temp_user_id, # Lưu cùng user_id cho tin nhắn AI? Hoặc để NULL?
            sender="assistant",
            content=ai_response_content,
            is_emergency=is_emergency_response
        )
        # Hiển thị tin nhắn AI (như cũ)
        with st.chat_message(name="assistant", avatar="🤖"):
            st.markdown(ai_response_content, unsafe_allow_html=is_emergency_response)
            st.caption(timestamp_ai.strftime('%H:%M:%S %d/%m/%Y'))
            if is_emergency_response:
                st.error("❗ Hãy ưu tiên liên hệ hỗ trợ khẩn cấp theo thông tin trên.")
    # ... (phần else như cũ) ...
    else:
         # Chỉ hiển thị cảnh báo nếu không phải lỗi kết nối DB đã báo trước đó
        if db_secrets: # Nếu cấu hình DB có vẻ ổn nhưng AI vẫn không phản hồi
             st.warning("Trợ Lý AI hiện không thể phản hồi. Vui lòng thử lại sau.")

# --- Sidebar ---
with st.sidebar:
    st.header("Công cụ khác")
    # !!! THAY BẰNG LINK THẬT ĐẾN CÁC TRANG KHÁC NẾU CÓ !!!
    st.markdown("- [📚 Thư viện Tài nguyên](#)")
    st.markdown("- [📅 Đặt lịch hẹn](#)")
    st.markdown("- [🔑 Admin Dashboard](#)") # Link tới trang admin nếu muốn

    st.divider()
    st.header("Hỗ trợ khẩn cấp")
    # !!! THAY BẰNG THÔNG TIN THẬT !!!
    st.markdown("- Đường dây nóng ABC: **[SỐ ĐIỆN THOẠI]**")
    st.markdown("- Tư vấn viên trường XYZ: **[LIÊN HỆ]**")
    st.divider()
    st.info("Trợ Lý Học Đường AI đang trong giai đoạn thử nghiệm.")
    st.warning("Lịch sử chat sẽ bị mất khi bạn đóng trình duyệt/tab.")
