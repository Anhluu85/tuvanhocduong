import streamlit as st
import datetime

st.set_page_config(page_title="AI Đồng Hành - Chat", layout="wide")

st.title("💬 AI Đồng Hành Học Đường")
st.caption("Người bạn AI lắng nghe và hỗ trợ bạn")

# --- Khởi tạo lịch sử chat trong Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Hiển thị lời chào và giới thiệu ban đầu ---
if not st.session_state.messages: # Chỉ hiển thị nếu lịch sử trống
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(
            "Xin chào! Mình là AI Đồng Hành, ở đây để lắng nghe và hỗ trợ bạn. "
            "Mình có thể cung cấp thông tin, gợi ý giải pháp cho các vấn đề học đường thường gặp. 😊"
        )
        st.markdown(
             "**Lưu ý:** Mình chỉ là AI hỗ trợ, không thay thế chuyên gia tâm lý. "
             "Nếu bạn đang gặp khủng hoảng, hãy liên hệ ngay với người lớn tin cậy hoặc [Đường dây nóng hỗ trợ](#). <span style='color:red; font-weight:bold;'>(Cần thay link/số thật)</span>",
            unsafe_allow_html=True
        )
        # Thêm nút gợi ý nếu muốn
        # cols = st.columns(3)
        # if cols[0].button("Giúp về học tập"): st.session_state.topic = "học tập" # Ví dụ lưu chủ đề
        # if cols[1].button("Giảm căng thẳng"): st.session_state.topic = "căng thẳng"
        # if cols[2].button("Tìm hiểu ngành nghề"): st.session_state.topic = "nghề nghiệp"


# --- Hiển thị các tin nhắn đã có trong lịch sử ---
for message in st.session_state.messages:
    role = message["role"]
    avatar = "🧑‍🎓" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])
        # Hiển thị timestamp nếu có
        if "timestamp" in message:
             st.caption(message["timestamp"].strftime('%H:%M:%S %d/%m/%Y'))


# --- Ô nhập liệu và xử lý input mới ---
prompt = st.chat_input("Bạn đang nghĩ gì? Hãy chia sẻ với mình...")

if prompt:
    # 1. Hiển thị tin nhắn người dùng
    timestamp_user = datetime.datetime.now()
    user_message = {"role": "user", "content": prompt, "timestamp": timestamp_user}
    st.session_state.messages.append(user_message)
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
        st.caption(timestamp_user.strftime('%H:%M:%S %d/%m/%Y'))

    # 2. Tạo phản hồi từ AI (Hiện tại chỉ là phản hồi giả lập)
    # !!! THAY THẾ PHẦN NÀY BẰNG LOGIC GỌI AI THẬT SỰ !!!
    timestamp_ai = datetime.datetime.now()
    ai_response_content = f"AI đang xử lý: '{prompt}'... (Đây là phản hồi demo)"

    # Giả lập thêm 1 phản hồi khác
    if "học" in prompt.lower():
        ai_response_content += "\n\nMình thấy bạn nhắc đến việc học. Bạn có muốn tìm hiểu về cách tập trung hay quản lý thời gian không?"
    elif "buồn" in prompt.lower() or "căng thẳng" in prompt.lower():
         ai_response_content += "\n\nMình hiểu bạn đang không vui. Hãy thử hít thở sâu 3 lần xem sao nhé?"


    # 3. Hiển thị và lưu tin nhắn AI
    ai_message = {"role": "assistant", "content": ai_response_content, "timestamp": timestamp_ai}
    st.session_state.messages.append(ai_message)
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(ai_response_content)
        st.caption(timestamp_ai.strftime('%H:%M:%S %d/%m/%Y'))

    # Tự động cuộn xuống dưới cùng (có thể cần reload nhẹ trang)
    # Streamlit thường tự xử lý việc này khá tốt với chat_input/chat_message

# --- (Tùy chọn) Thanh bên với các liên kết ---
with st.sidebar:
    st.header("Công cụ khác")
    st.page_link("pages/📚_Thư_viện_Tài_nguyên.py", label="📚 Thư viện Tài nguyên") # Giả sử có trang này
    st.page_link("pages/📅_Đặt_lịch_hẹn.py", label="📅 Đặt lịch hẹn") # Giả sử có trang này
    st.divider()
    st.header("Hỗ trợ khẩn cấp")
    # !!! THAY BẰNG THÔNG TIN THẬT !!!
    st.markdown("- Đường dây nóng ABC: [Số điện thoại]")
    st.markdown("- Tư vấn viên trường XYZ: [Thông tin liên hệ]")
