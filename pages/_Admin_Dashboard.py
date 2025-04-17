import streamlit as st
import pandas as pd # Thư viện để hiển thị bảng đẹp hơn (cần thêm vào requirements.txt)
import hashlib # Để hash mật khẩu (vẫn không đủ an toàn cho production)

# --- CẢNH BÁO BẢO MẬT NGHIÊM TRỌNG ---
# Cách xác thực này chỉ dùng cho DEMO SIÊU CƠ BẢN.
# KHÔNG BAO GIỜ dùng cách này trong môi trường thực tế.
# Hãy dùng thư viện streamlit-authenticator hoặc giải pháp chuyên nghiệp hơn.
# Mật khẩu nên được lưu trữ an toàn (hashed + salted) trong CSDL hoặc secrets.
CORRECT_PASSWORD_HASH = "YOUR_STRONG_PASSWORD_HASH_HERE" # Thay bằng hash của mật khẩu admin thật sự
                                                          # Ví dụ tạo hash: hashlib.sha256("your_password".encode()).hexdigest()

def check_password():
    """Trả về True nếu mật khẩu đúng, False nếu sai."""
    st.sidebar.title("🔒 Đăng nhập Admin")
    password = st.sidebar.text_input("Nhập mật khẩu Admin:", type="password")

    if not password:
        st.warning("Vui lòng nhập mật khẩu để truy cập trang Admin.")
        st.stop() # Dừng thực thi nếu chưa nhập mật khẩu

    # Hash mật khẩu người dùng nhập và so sánh
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash == CORRECT_PASSWORD_HASH:
        st.sidebar.success("Đăng nhập thành công!")
        return True
    else:
        st.sidebar.error("Mật khẩu không chính xác.")
        st.stop() # Dừng thực thi nếu sai mật khẩu

# --- Bắt đầu trang Admin ---
st.set_page_config(page_title="Admin Dashboard", layout="wide") # Layout rộng hơn

# Kiểm tra mật khẩu trước khi hiển thị nội dung
if not check_password():
    st.stop() # Dừng nếu mật khẩu sai

st.title("📊 Bảng điều khiển Admin - AI Đồng Hành Học Đường")
st.write("Chào mừng đến trang quản trị!")

# --- DỮ LIỆU MẪU (Sẽ thay bằng dữ liệu từ CSDL thật) ---
dummy_conversations_count = 125
dummy_alerts_count = 5
dummy_popular_topics = {"Học tập": 40, "Thi cử": 25, "Hướng nghiệp": 15, "Tâm lý": 10, "Khác": 10}
dummy_alerts = [
    {"id": "chat_123", "timestamp": "2023-10-27 10:15:00", "reason": "Từ khóa tự hại", "snippet": "...cảm thấy không muốn sống nữa...", "status": "Mới"},
    {"id": "chat_456", "timestamp": "2023-10-27 09:30:00", "reason": "Lo âu cao độ", "snippet": "...áp lực thi cử quá lớn, mình không chịu nổi...", "status": "Đang xử lý"},
    {"id": "chat_789", "timestamp": "2023-10-26 15:00:00", "reason": "Bạo lực học đường", "snippet": "...bị bạn bè bắt nạt...", "status": "Đã giải quyết"},
]

# --- Hiển thị Dashboard ---
st.header("📈 Tổng quan")
col1, col2, col3 = st.columns(3)
col1.metric("Tổng số cuộc trò chuyện (Tuần)", dummy_conversations_count)
col2.metric("Số cảnh báo mới", len([a for a in dummy_alerts if a['status'] == 'Mới']))
col3.metric("Chủ đề phổ biến nhất", max(dummy_popular_topics, key=dummy_popular_topics.get()))

st.subheader("Chủ đề quan tâm")
# Chuyển dict thành DataFrame để vẽ biểu đồ
topic_df = pd.DataFrame(list(dummy_popular_topics.items()), columns=['Chủ đề', 'Số lượng'])
st.bar_chart(topic_df.set_index('Chủ đề'))


# --- Quản lý Cảnh báo ---
st.header("🚨 Quản lý Cảnh báo")
st.write("Các cuộc trò chuyện cần chú ý đặc biệt.")

# Tạo DataFrame từ dữ liệu mẫu
alerts_df = pd.DataFrame(dummy_alerts)

# Bộ lọc (ví dụ đơn giản)
status_filter = st.selectbox("Lọc theo trạng thái:", ["Tất cả"] + list(alerts_df['status'].unique()))

if status_filter != "Tất cả":
    filtered_alerts_df = alerts_df[alerts_df['status'] == status_filter]
else:
    filtered_alerts_df = alerts_df

st.dataframe(filtered_alerts_df, use_container_width=True) # Hiển thị bảng dữ liệu

# Ví dụ về cách xem chi tiết (chưa có action thật)
selected_alert_id = st.selectbox("Chọn ID cảnh báo để xem (ví dụ):", [""] + list(alerts_df['id']))
if selected_alert_id:
    selected_data = alerts_df[alerts_df['id'] == selected_alert_id].iloc[0]
    st.write("--- Chi tiết cảnh báo ---")
    st.write(f"**ID:** {selected_data['id']}")
    st.write(f"**Thời gian:** {selected_data['timestamp']}")
    st.write(f"**Lý do:** {selected_data['reason']}")
    st.write(f"**Trích đoạn:** {selected_data['snippet']}")
    st.write(f"**Trạng thái:** {selected_data['status']}")
    if st.button(f"Đánh dấu 'Đang xử lý' cho {selected_alert_id}"):
        # Chỗ này bạn sẽ code logic cập nhật trạng thái vào CSDL thật
        st.success(f"Đã cập nhật trạng thái (DEMO). Cần code logic CSDL.")
    if st.button(f"Đánh dấu 'Đã giải quyết' cho {selected_alert_id}"):
        # Chỗ này bạn sẽ code logic cập nhật trạng thái vào CSDL thật
        st.success(f"Đã cập nhật trạng thái (DEMO). Cần code logic CSDL.")
    st.write("---")


# --- Các phần khác (Cần xây dựng thêm) ---
st.header("📚 Quản lý Cơ sở Kiến thức (Chưa xây dựng)")
st.info("Tính năng này cần được phát triển để thêm/sửa/xóa câu hỏi, tài liệu cho AI.")

st.header("👤 Quản lý Người dùng Admin (Chưa xây dựng)")
st.info("Tính năng này cần được phát triển để quản lý tài khoản và phân quyền admin.")

st.header("💬 Xem lại Lịch sử Chat (Chưa xây dựng - Cần cân nhắc kỹ về quyền riêng tư)")
st.warning("Tính năng này rất nhạy cảm, cần xây dựng cơ chế kiểm soát truy cập chặt chẽ.")
