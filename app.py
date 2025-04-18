# --- START OF FILE app.py ---

# app.py

import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import datetime
import psycopg2 # Để tương tác với PostgreSQL (Neon)
import pandas as pd # Vẫn cần cho một số xử lý dữ liệu
import uuid # << --- THÊM IMPORT NÀY ---

# --- Cấu hình cơ bản ---
st.set_page_config(
    page_title="Trợ Lý Học Đường AI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Trợ Lý Học Đường AI")
st.caption("Hỏi đáp cùng AI về học tập, nghề nghiệp, cảm xúc và các khó khăn trong đời sống học đường.")

# --- Quản lý API Key và Cấu hình ---
load_dotenv()
google_api_key = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))
if not google_api_key:
    st.error("Lỗi: Không tìm thấy GOOGLE_API_KEY.")
    st.stop()

db_secrets = st.secrets.get("database")
if not db_secrets:
    st.error("Lỗi: Không tìm thấy cấu hình [database].")
    # Cân nhắc có nên st.stop() hay không

# --- Khởi tạo Mô hình Gemini ---
try:
    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"Lỗi khởi tạo mô hình Gemini: {e}")
    print(f"Gemini Initialization Error: {e}")
    st.stop()

# --- Phần Kết nối và Tương tác CSDL ---
@st.cache_resource(ttl=600)
def connect_db():
    """Kết nối đến CSDL PostgreSQL."""
    print("Attempting to connect to the database...")
    if not db_secrets:
        print("DB connection info missing in secrets.")
        return None
    try:
        if "uri" in db_secrets:
            conn = psycopg2.connect(db_secrets["uri"])
        elif "host" in db_secrets:
            conn = psycopg2.connect(
                host=db_secrets["host"], port=db_secrets.get("port", 5432),
                dbname=db_secrets["dbname"], user=db_secrets["user"],
                password=db_secrets["password"], sslmode=db_secrets.get("sslmode", "require")
            )
        else:
            print("DB connection info incomplete in secrets.")
            return None
        print("Database connection successful!")
        return conn
    except psycopg2.OperationalError as e:
         print(f"DB Connection OperationalError: {e}. Check credentials, host, port, network, SSL.")
         # Không hiển thị lỗi trên UI để tránh làm lộ thông tin
         # st.error("Lỗi kết nối CSDL. Vui lòng thử lại sau.")
         return None
    except Exception as e:
        print(f"DB Connection Error: {e}")
        # st.error("Lỗi kết nối CSDL. Vui lòng thử lại sau.")
        return None

# --- Hàm tạo/lấy Session ID --- >> THÊM HÀM NÀY
def get_session_id():
    """Tạo hoặc lấy session_id duy nhất cho phiên hiện tại."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        print(f"Generated new session ID: {st.session_state.session_id}")
    return st.session_state.session_id

# --- Hàm tạo Alert trong DB (Đã sửa, không dùng user_id_associated trong INSERT) ---
def create_alert_in_db(session_id, reason, snippet, priority, status='Mới', user_id_associated=None): # Tham số user_id_associated vẫn nhận nhưng không dùng trong INSERT
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
        print(f"Creating alert: session={session_id}, reason='{reason}', priority={priority}, user(ignored)={user_id_associated}") # Log cả user_id nhận vào

        # Câu lệnh INSERT đã được sửa để KHÔNG chứa cột user_id_associated
        sql = """
            INSERT INTO alerts (chat_session_id, reason, snippet, priority, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id -- (Tùy chọn) Có thể lấy lại ID nếu cần
        """
        cursor.execute(sql, (session_id, reason, snippet, priority, status)) # Chỉ truyền các giá trị tương ứng
        alert_id = cursor.fetchone()[0] if cursor.rowcount > 0 else None # Lấy ID nếu có RETURNING

        conn.commit()
        alert_created = True
        print(f"Alert created successfully with ID: {alert_id} for session {session_id}.")
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

# --- Hàm Lưu lịch sử chat ---
def save_message_to_db(session_id, user_id, sender, content, is_greeting=False, is_emergency=False):
    """Lưu một tin nhắn vào bảng 'conversations'."""
    conn = connect_db()
    if conn is None:
        print("Error saving message: No DB connection.")
        return False
    cursor = None
    saved = False
    try:
        cursor = conn.cursor()
        print(f"Saving message: session={session_id}, user={user_id}, sender={sender}")
        # KIỂM TRA TÊN CỘT TRONG CSDL: session_id, user_id, sender, message_content, is_greeting, is_emergency
        sql = """
            INSERT INTO conversations (session_id, user_id, sender, message_content, is_greeting, is_emergency)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (session_id, user_id, sender, content, is_greeting, is_emergency))
        conn.commit()
        saved = True
        print("Message saved successfully.")
    except Exception as e:
        if conn: conn.rollback()
        print(f"--- DATABASE ERROR Saving Message ---")
        print(f"Session: {session_id}, User: {user_id}, Sender: {sender}")
        print(f"Error: {e}, Type: {type(e).__name__}")
        print(f"-----------------------------------")
    finally:
        if cursor: cursor.close()
    return saved

# --- Phần Logic Nhận diện Rủi ro ---
RISK_KEYWORDS = { # CẦN MỞ RỘNG DANH SÁCH NÀY
    "tự hại": ["muốn chết", "kết thúc", "tự tử", "không muốn sống", "tự làm đau", "dao kéo", "tuyệt vọng"],
    "bạo lực": ["bị đánh", "bị đập", "bị trấn", "bị đe dọa", "bắt nạt hội đồng"],
}
def detect_risk(text):
    text_lower = text.lower()
    for risk_type, keywords in RISK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                print(f"!!! RISK DETECTED: Type={risk_type}, Keyword='{keyword}'")
                return risk_type
    return None

def get_emergency_response_message(risk_type):
    emergency_contacts = """
- Đường dây nóng ABC: **[SỐ ĐIỆN THOẠI THẬT]**
- Tư vấn viên trường XYZ: **[THÔNG TIN LIÊN HỆ THẬT]**
- Hoặc nói chuyện ngay với thầy/cô/người lớn mà bạn tin tưởng nhất."""
    base_message = f"Mình nhận thấy bạn đang đề cập đến một vấn đề rất nghiêm trọng ({risk_type}). Sự an toàn của bạn là quan trọng nhất lúc này. " \
                   f"Mình là AI và không thể thay thế sự hỗ trợ trực tiếp từ chuyên gia. " \
                   f"Vui lòng liên hệ ngay các nguồn trợ giúp sau đây nhé:\n{emergency_contacts}"
    return base_message

# --- Quản lý Session Chat Gemini và Lịch sử Hiển thị ---
# >> GỌI HÀM ĐỂ ĐẢM BẢO SESSION ID ĐƯỢC TẠO/LẤY <<
current_session_id = get_session_id()
# st.sidebar.caption(f"Session ID (for debug): {current_session_id}") # Hiển thị để debug nếu cần

if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []
    print("Initialized empty display history.")
if "api_chat_session" not in st.session_state:
    st.session_state.api_chat_session = None
    print("API Chat Session placeholder created.")

def get_api_chat_session():
    if st.session_state.api_chat_session is None:
        print("API chat session is None, attempting to initialize...")
        try:
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
            return None
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
    greeting_message = {"role": "assistant", "content": greeting_content, "timestamp": timestamp_greet, "is_greeting": True}
    st.session_state.gemini_history.append(greeting_message)
    print("Added initial greeting message to display history.")
    # >> LƯU LỜI CHÀO VÀO DB <<
    # Tạo user_id ẩn danh ngay khi có tin nhắn đầu tiên
    if "anonymous_user_id" not in st.session_state:
         st.session_state.anonymous_user_id = f"anon-{str(uuid.uuid4())[:8]}"
         print(f"Generated anonymous user ID: {st.session_state.anonymous_user_id}")
    save_message_to_db(
        session_id=current_session_id,
        user_id=st.session_state.anonymous_user_id, # Dùng user_id ẩn danh
        sender="assistant",
        content=greeting_content,
        is_greeting=True
    )

# 2. Hiển thị lịch sử chat
for message in st.session_state.gemini_history:
    role = message["role"]
    avatar = "🧑‍🎓" if role == "user" else "🤖"
    with st.chat_message(name=role, avatar=avatar):
        allow_html = message.get("is_greeting", False) or message.get("is_emergency", False)
        st.markdown(message["content"], unsafe_allow_html=allow_html)
        if "timestamp" in message:
             st.caption(message["timestamp"].strftime('%H:%M:%S %d/%m/%Y'))
        if message.get("is_emergency", False):
             st.error("❗ Hãy ưu tiên liên hệ hỗ trợ khẩn cấp theo thông tin trên.")

# 3. Ô nhập liệu và xử lý
user_prompt = st.chat_input("Nhập câu hỏi hoặc điều bạn muốn chia sẻ...")

if user_prompt:
    # --- Lấy session_id --- >> LẤY TỪ BIẾN ĐÃ CÓ <<
    session_id_to_save = current_session_id

    # --- Tạo hoặc lấy User ID ẩn danh --- >> LẤY TỪ SESSION STATE <<
    if "anonymous_user_id" not in st.session_state:
         st.session_state.anonymous_user_id = f"anon-{str(uuid.uuid4())[:8]}"
         print(f"Generated anonymous user ID: {st.session_state.anonymous_user_id}")
    user_id_to_save = st.session_state.anonymous_user_id
    # ------------------------------------------

    # a. Lưu và Hiển thị tin nhắn người dùng
    timestamp_user = datetime.datetime.now()
    user_message = {"role": "user", "content": user_prompt, "timestamp": timestamp_user}
    st.session_state.gemini_history.append(user_message)
    save_message_to_db( # >> LƯU VÀO DB <<
        session_id=session_id_to_save,
        user_id=user_id_to_save,
        sender="user",
        content=user_prompt
    )
    with st.chat_message(name="user", avatar="🧑‍🎓"):
        st.markdown(user_prompt)
        st.caption(timestamp_user.strftime('%H:%M:%S %d/%m/%Y'))

    # b. Xử lý prompt: Kiểm tra rủi ro trước
    ai_response_content = None
    is_emergency_response = False
    detected_risk = detect_risk(user_prompt)

    with st.spinner("Trợ lý AI đang xử lý..."):
        if detected_risk:
            is_emergency_response = True
            ai_response_content = get_emergency_response_message(detected_risk)
            # Tạo cảnh báo trong DB (dùng ID ẩn danh)
            create_alert_in_db( # >> GỌI HÀM TẠO ALERT <<
                session_id=session_id_to_save,
                reason=f"Phát hiện rủi ro: {detected_risk}",
                snippet=user_prompt[:500],
                priority=1,
                user_id_associated=user_id_to_save # Truyền ID ẩn danh vào đây
            )
        else:
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
        ai_message = {"role": "assistant", "content": ai_response_content, "timestamp": timestamp_ai, "is_emergency": is_emergency_response}
        st.session_state.gemini_history.append(ai_message)
        save_message_to_db( # >> LƯU VÀO DB <<
            session_id=session_id_to_save,
            user_id=user_id_to_save,
            sender="assistant",
            content=ai_response_content,
            is_emergency=is_emergency_response
        )
        with st.chat_message(name="assistant", avatar="🤖"):
            st.markdown(ai_response_content, unsafe_allow_html=is_emergency_response)
            st.caption(timestamp_ai.strftime('%H:%M:%S %d/%m/%Y'))
            if is_emergency_response:
                st.error("❗ Hãy ưu tiên liên hệ hỗ trợ khẩn cấp theo thông tin trên.")
    else:
        if db_secrets:
             st.warning("Trợ Lý AI hiện không thể phản hồi. Vui lòng thử lại sau.")

# --- Sidebar ---
with st.sidebar:
    st.header("Công cụ khác")
    st.markdown("- [📚 Thư viện Tài nguyên](#)") # Thay link thật
    st.markdown("- [📅 Đặt lịch hẹn](#)")     # Thay link thật
    st.markdown("- [🔑 Admin Dashboard](#)") # Thay link thật nếu có trang riêng

    st.divider()
    st.header("Hỗ trợ khẩn cấp")
    st.markdown("- Đường dây nóng ABC: **[SỐ ĐIỆN THOẠI]**") # Thay số thật
    st.markdown("- Tư vấn viên trường XYZ: **[LIÊN HỆ]**") # Thay liên hệ thật
    st.divider()
    st.info("Trợ Lý Học Đường AI đang trong giai đoạn thử nghiệm.")
    # st.sidebar.caption(f"Session ID: {current_session_id}") # Bỏ comment nếu muốn debug session id

# --- END OF FILE app.py ---
