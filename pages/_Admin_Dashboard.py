# pages/🔑_Admin_Dashboard.py

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import os
import datetime # Thêm để xử lý thời gian nếu cần
import psycopg2 # <--- THÊM DÒNG NÀY
# --- Cấu hình trang ---
# Phải là lệnh Streamlit đầu tiên
st.set_page_config(page_title="Admin Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Đọc cấu hình xác thực ---
# (Giữ nguyên code đọc config.yaml và xử lý lỗi như trước)
config = None
config_path = 'config.yaml'
try:
    if os.path.exists(config_path):
        with open(config_path) as file:
            config = yaml.load(file, Loader=SafeLoader)
    else:
        st.error(f"Lỗi: Không tìm thấy file cấu hình tại '{config_path}'.")
        st.stop()
except Exception as e:
    st.error(f"Lỗi đọc/phân tích config.yaml: {e}")
    st.stop()

if not config:
    st.error("Lỗi: Không tải được cấu hình.")
    st.stop()

# --- Lấy Cookie Key từ Secrets ---
# (Giữ nguyên code lấy cookie_key và xử lý lỗi như trước)
cookie_key = None
try:
    cookie_key = st.secrets["cookie"]["key"]
    if not cookie_key or len(cookie_key) < 32:
        raise ValueError("Cookie key không hợp lệ.")
except Exception as e:
     st.error(f"Lỗi cấu hình Cookie Key: {e}")
     st.stop()

# --- Khởi tạo đối tượng Authenticator ---
# (Giữ nguyên code khởi tạo authenticator và xử lý lỗi như trước)
authenticator = None
try:
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        cookie_key,
        config['cookie']['expiry_days']
    )
except Exception as e:
    st.error(f"Lỗi khởi tạo Authenticator: {e}")
    st.stop()

if not authenticator:
     st.error("Lỗi: Không khởi tạo được Authenticator.")
     st.stop()

# --- Hiển thị Form Đăng nhập ---
name, authentication_status, username = authenticator.login('main')

# --- Xử lý trạng thái đăng nhập ---
if authentication_status is False:
    st.error('Tên đăng nhập/mật khẩu không chính xác')
    st.stop()
elif authentication_status is None:
    st.warning('Vui lòng nhập tên đăng nhập và mật khẩu')
    st.stop()
elif authentication_status: # Đăng nhập thành công
    # --- BẮT ĐẦU NỘI DUNG CHÍNH CỦA TRANG ADMIN ---
    st.sidebar.success(f"Xin chào, **{name}**!")
    authenticator.logout('Đăng xuất', 'sidebar') # Đổi chữ thành tiếng Việt

    st.title("📊 Bảng điều khiển Admin - AI Đồng Hành Học Đường")
    st.markdown("---")

    # --- PHẦN TƯƠNG TÁC CSDL (CẦN THAY THẾ BẰNG LOGIC THẬT) ---
    # Ví dụ hàm kết nối (Cần triển khai thực tế)
    @st.cache_resource
    def connect_db():
        try:
            # Ưu tiên đọc URI nếu có
            if "uri" in st.secrets.get("database", {}):
                 conn_uri = st.secrets["database"]["uri"]
                 conn = psycopg2.connect(conn_uri)
            # Nếu không có URI, dùng các tham số riêng lẻ
            elif "host" in st.secrets.get("database", {}):
                 db_creds = st.secrets["database"]
                 conn = psycopg2.connect(
                     host=db_creds["host"],
                     port=db_creds.get("port", 5432), # Dùng get để có giá trị mặc định
                     dbname=db_creds["dbname"],
                     user=db_creds["user"],
                     password=db_creds["password"],
                     sslmode=db_creds.get("sslmode", "require") # Mặc định require
                 )
            else:
                st.error("Thiếu thông tin kết nối CSDL trong Streamlit Secrets.")
                return None
    
            # st.success("Kết nối Neon PostgreSQL thành công!") # Bỏ comment khi test
            return conn
        except Exception as e:
            st.error(f"Lỗi kết nối Neon DB: {e}")
            return None
    
    db_connection = connect_db()
    # Ví dụ các hàm lấy/cập nhật dữ liệu (Cần triển khai thực tế)
    def fetch_dashboard_stats(conn):
        # --- VIẾT CODE TRUY VẤN CSDL ĐỂ LẤY THỐNG KÊ ---
        # Ví dụ: Đếm số cuộc trò chuyện, số cảnh báo mới,...
        # Trả về một dictionary hoặc object chứa các số liệu
        if conn:
             # cursor = conn.cursor()
             # cursor.execute("SELECT COUNT(*) FROM conversations WHERE date > NOW() - interval '7 day'")
             # weekly_chats = cursor.fetchone()[0]
             # cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Mới'")
             # new_alerts = cursor.fetchone()[0]
             # return {"weekly_chats": weekly_chats, "new_alerts": new_alerts, "popular_topic": "Học tập (Demo)"}
             pass # Bỏ qua nếu chưa có code
        # Dữ liệu giả lập nếu chưa có CSDL
        return {"weekly_chats": 150, "new_alerts": 3, "popular_topic": "Thi cử (Demo)"}

    def fetch_alerts(conn, status_filter=None):
        # --- VIẾT CODE TRUY VẤN CSDL ĐỂ LẤY DANH SÁCH CẢNH BÁO ---
        # Có thể lọc theo status_filter nếu được cung cấp
        # Trả về Pandas DataFrame hoặc list of dictionaries
        if conn:
             # query = "SELECT id, timestamp, reason, snippet, status, assignee FROM alerts"
             # params = []
             # if status_filter and status_filter != "Tất cả":
             #     query += " WHERE status = %s"
             #     params.append(status_filter)
             # query += " ORDER BY timestamp DESC"
             # df = pd.read_sql(query, conn, params=params)
             # return df
             pass
        # Dữ liệu giả lập
        dummy_alerts_list = [
            {"id": "chat_123", "timestamp": datetime.datetime(2023, 10, 27, 10, 15), "reason": "Từ khóa tự hại", "snippet": "...cảm thấy không muốn sống nữa...", "status": "Mới", "assignee": None},
            {"id": "chat_456", "timestamp": datetime.datetime(2023, 10, 27, 9, 30), "reason": "Lo âu cao độ", "snippet": "...áp lực thi cử quá lớn...", "status": "Đang xử lý", "assignee": "Admin Trường"},
            {"id": "chat_789", "timestamp": datetime.datetime(2023, 10, 26, 15, 0), "reason": "Bạo lực", "snippet": "...bị bạn bè bắt nạt...", "status": "Đã giải quyết", "assignee": "Admin Trường"},
            {"id": "chat_101", "timestamp": datetime.datetime(2023, 10, 28, 11, 0), "reason": "Từ khóa trầm cảm", "snippet": "...buồn chán không rõ lý do...", "status": "Mới", "assignee": None},
        ]
        df = pd.DataFrame(dummy_alerts_list)
        if status_filter and status_filter != "Tất cả":
            return df[df['status'] == status_filter]
        return df

    def update_alert_status_in_db(conn, alert_id, new_status, assignee):
        # --- VIẾT CODE CẬP NHẬT TRẠNG THÁI CẢNH BÁO TRONG CSDL ---
        # Trả về True nếu thành công, False nếu thất bại
        st.info(f"(Demo) Cập nhật CSDL: ID={alert_id}, Status={new_status}, Assignee={assignee}")
        if conn:
            try:
                # cursor = conn.cursor()
                # cursor.execute("UPDATE alerts SET status = %s, assignee = %s WHERE id = %s", (new_status, assignee, alert_id))
                # conn.commit() # Lưu thay đổi
                # return True
                pass
            except Exception as e:
                st.error(f"Lỗi CSDL khi cập nhật cảnh báo: {e}")
                # conn.rollback() # Hoàn tác nếu có lỗi
                return False
        return True # Giả lập thành công

    # --- KẾT THÚC PHẦN TƯƠNG TÁC CSDL ---


    # --- Kiểm tra kết nối CSDL ---
    if db_connection is None:
        st.error("Không thể kết nối đến Cơ sở dữ liệu. Các chức năng sẽ sử dụng dữ liệu giả lập hoặc bị hạn chế.")
        # Có thể chọn dừng ứng dụng ở đây nếu CSDL là bắt buộc: st.stop()

    # --- Hiển thị Dashboard Tổng quan ---
    st.header("📈 Tổng quan Hoạt động")
    stats = fetch_dashboard_stats(db_connection)
    col1, col2, col3 = st.columns(3)
    col1.metric("Cuộc trò chuyện (7 ngày)", stats.get("weekly_chats", "N/A"))
    col2.metric("Cảnh báo mới", stats.get("new_alerts", "N/A"))
    col3.metric("Chủ đề nổi bật", stats.get("popular_topic", "N/A"))
    # Thêm biểu đồ nếu cần, ví dụ:
    # st.line_chart(...) hoặc st.bar_chart(...)

    st.markdown("---")

    # --- Quản lý Cảnh báo ---
    st.header("🚨 Quản lý Cảnh báo")
    alerts_df = fetch_alerts(db_connection) # Lấy tất cả cảnh báo ban đầu

    if not alerts_df.empty:
        # Bộ lọc trạng thái
        status_list = ["Tất cả"] + list(alerts_df['status'].unique())
        selected_status = st.selectbox("Lọc theo trạng thái:", status_list)

        # Lọc DataFrame dựa trên lựa chọn
        if selected_status != "Tất cả":
            display_df = alerts_df[alerts_df['status'] == selected_status]
        else:
            display_df = alerts_df

        # Hiển thị bảng cảnh báo
        st.dataframe(display_df, use_container_width=True, hide_index=True) # Ẩn index cho gọn

        st.subheader("Xem và Cập nhật Cảnh báo")
        alert_ids = [""] + list(alerts_df['id'].unique()) # Thêm lựa chọn rỗng
        selected_alert_id = st.selectbox("Chọn ID cảnh báo để xử lý:", alert_ids)

        if selected_alert_id:
            selected_data = alerts_df[alerts_df['id'] == selected_alert_id].iloc[0]
            st.write(f"**Chi tiết cảnh báo ID:** `{selected_data['id']}`")
            st.write(f"**Thời gian:** {selected_data['timestamp']}")
            st.write(f"**Lý do:** {selected_data['reason']}")
            st.write(f"**Trích đoạn:**")
            st.text_area("Snippet", selected_data['snippet'], height=100, disabled=True) # Dùng text_area để xem dễ hơn

            # Form cập nhật
            with st.form(key=f"update_alert_{selected_alert_id}"):
                st.write("**Cập nhật trạng thái và người phụ trách:**")
                current_status_index = list(alerts_df['status'].unique()).index(selected_data['status'])
                new_status = st.selectbox("Trạng thái mới:", options=list(alerts_df['status'].unique()), index=current_status_index)
                assignee = st.text_input("Người phụ trách:", value=selected_data['assignee'] if pd.notna(selected_data['assignee']) else name) # Gán mặc định là admin đang login

                submitted = st.form_submit_button("Lưu thay đổi")
                if submitted:
                    # Gọi hàm cập nhật CSDL thực tế
                    success = update_alert_status_in_db(db_connection, selected_alert_id, new_status, assignee)
                    if success:
                        st.success(f"Đã cập nhật thành công cảnh báo {selected_alert_id}!")
                        # Rerun để làm mới bảng dữ liệu
                        st.experimental_rerun()
                    else:
                        st.error(f"Có lỗi xảy ra khi cập nhật cảnh báo {selected_alert_id}.")

    else:
        st.info("Hiện không có cảnh báo nào.")

    st.markdown("---")

    # --- Quản lý Cơ sở Kiến thức (Placeholder) ---
    st.header("📚 Quản lý Cơ sở Kiến thức")
    st.info("Tính năng này đang được phát triển.")
    # Ví dụ giao diện đơn giản để thêm FAQ
    with st.expander("Thêm câu hỏi thường gặp (FAQ) mới (Demo)"):
        new_question = st.text_input("Câu hỏi:")
        new_answer = st.text_area("Câu trả lời:")
        if st.button("Thêm FAQ"):
            if new_question and new_answer:
                # --- VIẾT CODE LƯU FAQ VÀO CSDL Ở ĐÂY ---
                st.success("(Demo) Đã thêm FAQ vào CSDL.")
            else:
                st.warning("Vui lòng nhập cả câu hỏi và câu trả lời.")


    st.markdown("---")

    # --- Các phần khác (Placeholder) ---
    st.header("👤 Quản lý Người dùng Admin")
    st.info("Hiện tại quản lý người dùng qua file `config.yaml`. Cần phát triển giao diện nếu muốn quản lý linh hoạt hơn.")

    st.header("💬 Xem lại Lịch sử Chat")
    st.warning("Tính năng này cần được xây dựng cẩn thận, đảm bảo quyền riêng tư và chỉ truy cập khi thực sự cần thiết cho mục đích gỡ lỗi hoặc điều tra sự cố an toàn.")

    # --- KẾT THÚC NỘI DUNG CHÍNH CỦA TRANG ADMIN ---
