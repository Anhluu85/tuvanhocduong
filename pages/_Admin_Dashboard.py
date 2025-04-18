# pages/🔑_Admin_Dashboard.py

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import os
import datetime # Thêm để xử lý thời gian nếu cần
import psycopg2 # Đảm bảo đã import

# --- Cấu hình trang ---
st.set_page_config(page_title="Admin Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Đọc cấu hình xác thực ---
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
cookie_key = None
try:
    cookie_key = st.secrets["cookie"]["key"]
    if not cookie_key or len(cookie_key) < 32:
        raise ValueError("Cookie key không hợp lệ.")
except Exception as e:
     st.error(f"Lỗi cấu hình Cookie Key: {e}")
     st.stop()

# --- Khởi tạo đối tượng Authenticator ---
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
# Sử dụng key khác nhau cho widget login ở các trang khác nhau nếu cần
# Hoặc dùng 'main' nếu chỉ có 1 form login chính
name, authentication_status, username = authenticator.login(key='admin_login_form') # Đặt key riêng cho form này

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
    authenticator.logout('Đăng xuất', 'sidebar', key='admin_logout_button') # Đặt key riêng

    st.title("📊 Bảng điều khiển Admin - AI Đồng Hành Học Đường")
    st.markdown("---")

    # --- PHẦN TƯƠNG TÁC CSDL ---
    @st.cache_resource(ttl=600) # Cache kết nối trong 10 phút
    def connect_db():
        """Kết nối đến CSDL PostgreSQL."""
        print("Attempting to connect to the database...") # Log
        try:
            if "uri" in st.secrets.get("database", {}):
                 conn_uri = st.secrets["database"]["uri"]
                 conn = psycopg2.connect(conn_uri)
            elif "host" in st.secrets.get("database", {}):
                 db_creds = st.secrets["database"]
                 conn = psycopg2.connect(
                     host=db_creds["host"],
                     port=db_creds.get("port", 5432),
                     dbname=db_creds["dbname"],
                     user=db_creds["user"],
                     password=db_creds["password"],
                     sslmode=db_creds.get("sslmode", "require")
                 )
            else:
                st.error("Thiếu thông tin kết nối CSDL trong Streamlit Secrets.")
                print("DB connection info missing in secrets.") # Log
                return None
            print("Database connection successful!") # Log
            return conn
        except psycopg2.OperationalError as e:
             st.error(f"Lỗi kết nối CSDL: Không thể kết nối tới server. Kiểm tra host, port, network, SSL và thông tin xác thực.")
             print(f"DB Connection OperationalError: {e}") # Log
             return None
        except Exception as e:
            st.error(f"Lỗi kết nối CSDL: {e}")
            print(f"DB Connection Error: {e}") # Log
            return None

    db_connection = connect_db()

    # --- Định nghĩa các hàm tương tác CSDL ---

    @st.cache_data(ttl=300) # Cache dữ liệu stats trong 5 phút
    def fetch_dashboard_stats(_conn): # Đổi tên tham số để tránh xung đột cache nếu dùng conn trực tiếp
        """Lấy các số liệu thống kê từ CSDL."""
        if _conn is None:
            return {"weekly_chats": "N/A", "new_alerts": "N/A", "popular_topic": "N/A"}

        print("Fetching dashboard stats from DB...") # Log
        stats = {"weekly_chats": "N/A", "new_alerts": "N/A", "popular_topic": "N/A"}
        cursor = None
        try:
            cursor = _conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Mới'")
            result_alerts = cursor.fetchone()
            stats["new_alerts"] = result_alerts[0] if result_alerts else 0

            # TODO: Implement weekly chats count (requires 'conversations' table with timestamp)
            stats["weekly_chats"] = "N/A"

            cursor.execute("""
                SELECT reason, COUNT(*) as count FROM alerts
                GROUP BY reason ORDER BY count DESC LIMIT 1
            """)
            popular = cursor.fetchone()
            stats["popular_topic"] = popular[0] if popular else "Không có"

            print(f"Fetched stats: {stats}") # Log
            return stats
        except Exception as e:
            st.error(f"Lỗi truy vấn thống kê: {e}")
            print(f"Error in fetch_dashboard_stats: {e}")
            return stats
        finally:
             if cursor: cursor.close()

    @st.cache_data(ttl=60) # Cache danh sách alerts trong 1 phút
    def fetch_alerts(_conn, status_filter=None):
        """Lấy danh sách cảnh báo từ CSDL."""
        if _conn is None:
             st.warning("Không có kết nối CSDL, không thể tải cảnh báo.")
             return pd.DataFrame() # Trả về rỗng nếu không có kết nối

        print(f"Fetching alerts from DB with filter: {status_filter}") # Log
        df = pd.DataFrame() # Khởi tạo df rỗng
        try:
            # KIỂM TRA LẠI TÊN CỘT CHO KHỚP CSDL CỦA BẠN
            query = "SELECT id, timestamp, reason, snippet, status, assignee, priority, chat_session_id FROM alerts"
            params = []
            if status_filter and status_filter != "Tất cả":
                query += " WHERE status = %s"
                params.append(status_filter)
            query += " ORDER BY timestamp DESC"

            df = pd.read_sql(query, _conn, params=params)
            print(f"Fetched {len(df)} alerts from DB.") # Log

            if not df.empty:
                if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                     df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Xử lý timezone nếu cần
            return df
        except Exception as e:
            st.error(f"LỖI fetch_alerts: Không thể tải danh sách cảnh báo. Chi tiết: {e}")
            print(f"Error fetching alerts: {e}")
            return df # Trả về df rỗng

    def update_alert_status_in_db(conn, alert_id, new_status, assignee):
        """Cập nhật trạng thái và người phụ trách của cảnh báo trong CSDL."""
        if conn is None: return False # Lỗi đã báo ở nơi khác
        cursor = None
        try:
            cursor = conn.cursor()
            print(f"Updating alert ID: {alert_id} to Status: {new_status}, Assignee: {assignee}") # Log
            # KIỂM TRA TÊN BẢNG/CỘT
            cursor.execute(
                "UPDATE alerts SET status = %s, assignee = %s WHERE id = %s",
                (new_status, assignee, alert_id)
            )
            conn.commit() # Lưu thay đổi
            if cursor.rowcount > 0:
                print(f"DB Update successful for alert ID {alert_id}.") # Log
                # Xóa cache của fetch_alerts để lấy dữ liệu mới
                st.cache_data.clear() # Xóa toàn bộ cache @st.cache_data (có thể ảnh hưởng hàm khác)
                # Hoặc nếu có cách xóa cache cụ thể cho fetch_alerts thì dùng (Streamlit có thể chưa hỗ trợ trực tiếp)
                # fetch_alerts.clear() # Lệnh này có thể không tồn tại trực tiếp
                return True
            else:
                st.warning(f"Không tìm thấy cảnh báo ID {alert_id} để cập nhật hoặc trạng thái không thay đổi.")
                conn.rollback()
                return False
        except Exception as e:
            if conn: conn.rollback()
            st.error(f"Lỗi CSDL khi cập nhật cảnh báo ID {alert_id}: {e}")
            print(f"Error updating alert {alert_id}: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def add_faq_to_db(conn, question, answer, category=None):
        """Thêm FAQ mới vào CSDL."""
        if conn is None: return False
        cursor = None
        try:
            cursor = conn.cursor()
            # KIỂM TRA TÊN BẢNG/CỘT
            print(f"Adding FAQ: Q='{question[:30]}...', Cat='{category}'") # Log
            cursor.execute(
                "INSERT INTO knowledge_base (question, answer, category) VALUES (%s, %s, %s)",
                (question, answer, category)
            )
            conn.commit()
            print("FAQ added successfully to DB.") # Log
            # Cần xóa cache nếu có hàm fetch_faqs
            # fetch_faqs.clear() # Ví dụ
            return True
        except Exception as e:
            if conn: conn.rollback()
            st.error(f"Lỗi CSDL khi thêm FAQ: {e}")
            print(f"Error adding FAQ: {e}")
            return False
        finally:
            if cursor: cursor.close()

    #@st.cache_data(ttl=300) # Cache lịch sử chat nếu cần
    def fetch_chat_history(_conn, session_id):
        """Lấy lịch sử chat cho một session_id cụ thể từ CSDL."""
        if _conn is None or not session_id:
            # st.warning("Yêu cầu Session ID để truy vấn lịch sử chat.")
            return pd.DataFrame()

        print(f"Fetching chat history for session: {session_id}") # Log
        df = pd.DataFrame()
        try:
            # KIỂM TRA TÊN BẢNG/CỘT
            query = """
                SELECT message_id, timestamp, sender, message_content, user_id -- Lấy các cột cần thiết
                FROM conversations
                WHERE session_id = %s
                ORDER BY timestamp ASC
            """
            df = pd.read_sql(query, _conn, params=(session_id,))
            print(f"Fetched {len(df)} messages for session {session_id}.") # Log

            if not df.empty:
                if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                     df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Xử lý timezone nếu cần
            return df
        except Exception as e:
            st.error(f"LỖI fetch_chat_history cho session {session_id}: {e}")
            print(f"Error fetching chat history for {session_id}: {e}")
            return df # Trả về rỗng

    # --- KẾT THÚC ĐỊNH NGHĨA HÀM CSDL ---

    # --- Kiểm tra kết nối và hiển thị nội dung chính ---
    if db_connection is None:
        st.warning("Không thể kết nối đến Cơ sở dữ liệu. Vui lòng kiểm tra cấu hình hoặc liên hệ quản trị viên.")
        # Có thể dừng ở đây hoặc hiển thị phần không cần DB
        st.stop()
    else:
        st.success("Đã kết nối Cơ sở dữ liệu thành công.")

        # --- Hiển thị Dashboard Tổng quan ---
        st.header("📈 Tổng quan Hoạt động")
        stats = fetch_dashboard_stats(db_connection)
        col1, col2, col3 = st.columns(3)
        col1.metric("Cuộc trò chuyện (7 ngày)", stats.get("weekly_chats", "N/A"))
        col2.metric("Cảnh báo mới", stats.get("new_alerts", "N/A"))
        col3.metric("Chủ đề nổi bật", stats.get("popular_topic", "N/A"))

        st.markdown("---")

        # --- Quản lý Cảnh báo ---
        st.header("🚨 Quản lý Cảnh báo")
        # Lấy dữ liệu alerts (sử dụng cache nếu fetch_alerts được cache)
        alerts_df = fetch_alerts(db_connection)

        if isinstance(alerts_df, pd.DataFrame) and not alerts_df.empty:
            st.info(f"Tìm thấy {len(alerts_df)} cảnh báo.")
            status_options = ["Tất cả", "Mới", "Đang xử lý", "Đã giải quyết"]
            selected_status = st.selectbox("Lọc theo trạng thái:", status_options, key="alert_status_filter")

            display_df = alerts_df.copy()
            if selected_status != "Tất cả":
                display_df = display_df[display_df['status'] == selected_status]

            st.dataframe(display_df, use_container_width=True, hide_index=True,
                         column_config={ # Định dạng cột timestamp
                             "timestamp": st.column_config.DatetimeColumn(
                                 "Thời gian",
                                 format="YYYY-MM-DD HH:mm:ss",
                             )
                         })

            st.subheader("Xem và Cập nhật Cảnh báo")
            alert_id_options = [""] + list(alerts_df['id'].astype(str).unique())
            selected_alert_id_str = st.selectbox("Chọn ID cảnh báo để xử lý:", alert_id_options, key="alert_id_select")

            if selected_alert_id_str:
                try:
                    selected_data_series = alerts_df[alerts_df['id'].astype(str) == selected_alert_id_str].iloc[0]
                    selected_data = selected_data_series.to_dict()

                    st.write(f"**Chi tiết cảnh báo ID:** `{selected_data.get('id', 'N/A')}`")
                    ts = selected_data.get('timestamp')
                    ts_display = ts.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(ts) else "N/A"
                    st.write(f"**Thời gian:** {ts_display}")
                    st.write(f"**Lý do:** {selected_data.get('reason', 'N/A')}")
                    st.write(f"**Trích đoạn:**")
                    st.text_area("Snippet", selected_data.get('snippet', ''), height=100, disabled=True, key=f"snippet_{selected_alert_id_str}")
                    st.write(f"**Độ ưu tiên:** {selected_data.get('priority', 'N/A')}")
                    st.write(f"**Session ID liên kết:** `{selected_data.get('chat_session_id', 'Không có')}`") # Hiển thị session id

                    with st.form(key=f"update_alert_form_{selected_alert_id_str}"):
                        st.write("**Cập nhật trạng thái và người phụ trách:**")
                        current_status = selected_data.get('status', 'Mới')
                        status_update_options = ["Mới", "Đang xử lý", "Đã giải quyết"] # Chỉ cho phép chọn trạng thái hợp lệ
                        try:
                            current_status_index = status_update_options.index(current_status)
                        except ValueError:
                            current_status_index = 0 # Mặc định về 'Mới'

                        new_status = st.selectbox("Trạng thái mới:", options=status_update_options, index=current_status_index, key=f"status_update_{selected_alert_id_str}")
                        current_assignee = selected_data.get('assignee')
                        default_assignee = name if pd.isna(current_assignee) else current_assignee
                        assignee = st.text_input("Người phụ trách:", value=default_assignee, key=f"assignee_{selected_alert_id_str}")

                        submitted = st.form_submit_button("Lưu thay đổi")
                        if submitted:
                            original_alert_id = selected_data.get('id')
                            if original_alert_id is not None:
                                success = update_alert_status_in_db(db_connection, original_alert_id, new_status, assignee)
                                if success:
                                    st.success(f"Đã gửi yêu cầu cập nhật cảnh báo {original_alert_id}!")
                                    st.rerun()
                            else:
                                st.error("Không thể xác định ID cảnh báo để cập nhật.")
                except IndexError:
                     st.warning(f"Không tìm thấy dữ liệu chi tiết cho ID: {selected_alert_id_str}")
                except Exception as e:
                     st.error(f"Lỗi khi hiển thị chi tiết cảnh báo: {e}")
                     print(f"Error rendering alert details {selected_alert_id_str}: {e}")

        elif db_connection is not None:
            st.info("Hiện không có cảnh báo nào trong cơ sở dữ liệu.")

        st.markdown("---")

        # --- Quản lý Cơ sở Kiến thức ---
        st.header("📚 Quản lý Cơ sở Kiến thức")
        # TODO: Thêm code fetch và hiển thị FAQ (ví dụ: dùng st.dataframe(fetch_faqs(db_connection)))
        st.info("Chức năng xem/sửa/xóa FAQ đang được phát triển.")

        with st.expander("Thêm câu hỏi thường gặp (FAQ) mới"):
            # Sử dụng key khác nhau cho widget trong expander
            new_question = st.text_input("Câu hỏi:", key="faq_new_question")
            new_answer = st.text_area("Câu trả lời:", key="faq_new_answer")
            new_category = st.text_input("Chủ đề (Category):", key="faq_new_category")
            if st.button("Thêm FAQ", key="faq_add_button"):
                if new_question and new_answer:
                    success = add_faq_to_db(db_connection, new_question, new_answer, new_category)
                    if success:
                        st.success("Đã thêm FAQ vào Cơ sở dữ liệu thành công!")
                        # Có thể rerun hoặc xóa cache của hàm fetch_faqs nếu có
                        # st.rerun()
                else:
                    st.warning("Vui lòng nhập cả câu hỏi và câu trả lời.")

        st.markdown("---")

        # --- Xem lại Lịch sử Chat ---
        st.header("💬 Xem lại Lịch sử Chat")
        st.warning("⚠️ Tính năng này chỉ dành cho mục đích gỡ lỗi và điều tra sự cố an toàn. Truy cập phải được ghi log và tuân thủ quy định bảo mật.")

        search_session_id = st.text_input("Nhập Session ID để xem lịch sử chat:", key="chat_session_search_input")

        # Lấy danh sách session_id từ các cảnh báo đã fetch
        linked_session_ids = [""]
        if isinstance(alerts_df, pd.DataFrame) and 'chat_session_id' in alerts_df.columns:
             valid_sessions = alerts_df[pd.notna(alerts_df['chat_session_id'])]['chat_session_id'].unique()
             linked_session_ids.extend(list(valid_sessions))
        selected_linked_session = st.selectbox("Hoặc chọn Session ID từ cảnh báo:", options=linked_session_ids, key="chat_session_select_box")

        session_id_to_fetch = search_session_id or selected_linked_session

        if session_id_to_fetch:
            st.write(f"Đang tải lịch sử cho Session ID: `{session_id_to_fetch}`")
            chat_history_df = fetch_chat_history(db_connection, session_id_to_fetch) # Sử dụng hàm đã định nghĩa

            if isinstance(chat_history_df, pd.DataFrame) and not chat_history_df.empty:
                st.write(f"**Lịch sử chat ({len(chat_history_df)} tin nhắn):**")
                # Hiển thị dạng chat message
                chat_container = st.container(height=400) # Đặt chiều cao cố định và thanh cuộn
                with chat_container:
                    for index, row in chat_history_df.iterrows():
                        role = "user" if str(row.get('sender', '')).lower() == 'user' else "assistant"
                        timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row.get('timestamp')) else ""
                        with st.chat_message(role, avatar= "🧑‍🎓" if role=='user' else "🤖"): # Thêm avatar đơn giản
                             st.markdown(row.get('message_content', ''))
                             st.caption(f"User: {row.get('user_id', 'Ẩn danh')} | Time: {timestamp_str}") # Cân nhắc ẩn user_id
            elif db_connection:
                st.info(f"Không tìm thấy lịch sử chat cho Session ID: {session_id_to_fetch}")

        st.markdown("---")

        # --- Các phần khác (Placeholder) ---
        st.header("👤 Quản lý Người dùng Admin")
        st.info("Hiện tại quản lý người dùng qua file `config.yaml`.")

# --- Kết thúc xử lý trạng thái đăng nhập ---
