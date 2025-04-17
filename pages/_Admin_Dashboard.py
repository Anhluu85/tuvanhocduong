import streamlit as st
import streamlit_authenticator as stauth # Import thư viện
import yaml                             # Import để đọc file YAML
from yaml.loader import SafeLoader      # Loader an toàn cho YAML
import pandas as pd

# --- Đọc cấu hình xác thực ---
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("Lỗi: Không tìm thấy file cấu hình 'config.yaml'.")
    st.stop()
except Exception as e:
    st.error(f"Lỗi khi đọc file config.yaml: {e}")
    st.stop()

# --- Lấy Cookie Key từ Secrets ---
# Rất quan trọng để bảo mật cookie key
try:
    cookie_key = st.secrets["cookie"]["key"]
    if not cookie_key or len(cookie_key) < 32:
         raise ValueError("Cookie key không hợp lệ trong secrets.")
except (KeyError, TypeError, ValueError) as e:
     st.error(f"Lỗi cấu hình Cookie Key trong Streamlit Secrets: {e}")
     st.warning("Vui lòng thêm 'key' (chuỗi ngẫu nhiên dài >= 32 ký tự) vào mục [cookie] trong Streamlit Secrets.")
     st.stop()


# --- Khởi tạo đối tượng Authenticator ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    cookie_key,  # Sử dụng key từ secrets
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# --- Hiển thị Form Đăng nhập ---
# Đặt tên biến `name`, `authentication_status`, `username` đúng như trong ví dụ của thư viện
name, authentication_status, username = authenticator.login('main')
# Tham số 'main' hoặc 'sidebar' để chọn vị trí form đăng nhập

# --- Kiểm tra Trạng thái Đăng nhập ---
if authentication_status is False:
    st.error('Tên đăng nhập/mật khẩu không chính xác')
    st.stop()
elif authentication_status is None:
    st.warning('Vui lòng nhập tên đăng nhập và mật khẩu')
    st.stop()
elif authentication_status: # Đăng nhập thành công
    # --- BẮT ĐẦU NỘI DUNG TRANG ADMIN (Chỉ hiển thị khi đã đăng nhập) ---
    st.set_page_config(page_title="Admin Dashboard", layout="wide")
    st.sidebar.success(f"Xin chào *{name}*") # Hiển thị tên người dùng đã đăng nhập
    authenticator.logout('Logout', 'sidebar') # Thêm nút Logout vào sidebar

    st.title("📊 Bảng điều khiển Admin - AI Đồng Hành Học Đường")
    st.write(f"Chào mừng *{name}* đến trang quản trị!")

    # --- DỮ LIỆU MẪU (Sẽ thay bằng dữ liệu từ CSDL thật - Bước sau) ---
    dummy_conversations_count = 125
    dummy_alerts_count = 5
    dummy_popular_topics = {"Học tập": 40, "Thi cử": 25, "Hướng nghiệp": 15, "Tâm lý": 10, "Khác": 10}
    dummy_alerts = [
        {"id": "chat_123", "timestamp": "2023-10-27 10:15:00", "reason": "Từ khóa tự hại", "snippet": "...cảm thấy không muốn sống nữa...", "status": "Mới", "assignee": None},
        {"id": "chat_456", "timestamp": "2023-10-27 09:30:00", "reason": "Lo âu cao độ", "snippet": "...áp lực thi cử quá lớn, mình không chịu nổi...", "status": "Đang xử lý", "assignee": "Tư vấn viên A"},
        {"id": "chat_789", "timestamp": "2023-10-26 15:00:00", "reason": "Bạo lực học đường", "snippet": "...bị bạn bè bắt nạt...", "status": "Đã giải quyết", "assignee": "Tư vấn viên B"},
    ]
    alerts_df = pd.DataFrame(dummy_alerts) # Tạo DataFrame sớm hơn

    # --- Hiển thị Dashboard ---
    st.header("📈 Tổng quan")
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số cuộc trò chuyện (Tuần)", dummy_conversations_count)
    col2.metric("Số cảnh báo mới", len(alerts_df[alerts_df['status'] == 'Mới']))
    col3.metric("Chủ đề phổ biến nhất", max(dummy_popular_topics, key=dummy_popular_topics.get()))

    st.subheader("Chủ đề quan tâm")
    topic_df = pd.DataFrame(list(dummy_popular_topics.items()), columns=['Chủ đề', 'Số lượng'])
    st.bar_chart(topic_df.set_index('Chủ đề'))


    # --- Quản lý Cảnh báo ---
    st.header("🚨 Quản lý Cảnh báo")
    st.write("Các cuộc trò chuyện cần chú ý đặc biệt.")

    status_filter = st.selectbox("Lọc theo trạng thái:", ["Tất cả"] + list(alerts_df['status'].unique()))
    if status_filter != "Tất cả":
        filtered_alerts_df = alerts_df[alerts_df['status'] == status_filter]
    else:
        filtered_alerts_df = alerts_df

    st.dataframe(filtered_alerts_df, use_container_width=True)

    selected_alert_id = st.selectbox("Chọn ID cảnh báo để xem/cập nhật:", [""] + list(alerts_df['id']))
    if selected_alert_id:
        selected_data = alerts_df[alerts_df['id'] == selected_alert_id].iloc[0]
        st.write("--- Chi tiết cảnh báo ---")
        st.write(f"**ID:** {selected_data['id']}")
        st.write(f"**Thời gian:** {selected_data['timestamp']}")
        st.write(f"**Lý do:** {selected_data['reason']}")
        st.write(f"**Trích đoạn:** {selected_data['snippet']}")
        # Giả lập các action - Bước sau sẽ là tương tác CSDL thật
        new_status = st.selectbox("Cập nhật trạng thái:", options=list(alerts_df['status'].unique()), index=list(alerts_df['status'].unique()).index(selected_data['status']))
        assignee = st.text_input("Người phụ trách:", value=selected_data['assignee'] if selected_data['assignee'] else "")

        if st.button(f"Lưu thay đổi cho {selected_alert_id}"):
            # BƯỚC SAU: Tại đây sẽ gọi hàm cập nhật CSDL thật sự
            st.success(f"Đã cập nhật trạng thái thành '{new_status}' và người phụ trách '{assignee}' cho {selected_alert_id} (DEMO).")
            # Sau khi cập nhật CSDL thành công, nên rerun lại để thấy thay đổi: st.experimental_rerun()

        st.write("---")

    # --- Các phần khác (Cần xây dựng thêm) ---
    st.header("📚 Quản lý Cơ sở Kiến thức (Chưa xây dựng)")
    # Nơi thêm code quản lý KB

    st.header("👤 Quản lý Người dùng Admin (Chưa xây dựng)")
    # Nơi thêm code quản lý user admin (nếu cần giao diện)

    st.header("💬 Xem lại Lịch sử Chat (Chưa xây dựng - Cần cân nhắc kỹ về quyền riêng tư)")
    # Nơi thêm code xem lịch sử chat

    # --- KẾT THÚC NỘI DUNG TRANG ADMIN ---
