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
    # ... (code đọc config.yaml như cũ) ...
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
    # ... (code lấy cookie_key như cũ) ...
    cookie_key = st.secrets["cookie"]["key"]
    if not cookie_key or len(cookie_key) < 32:
        raise ValueError("Cookie key không hợp lệ.")
except Exception as e:
     st.error(f"Lỗi cấu hình Cookie Key: {e}")
     st.stop()

# --- Khởi tạo đối tượng Authenticator ---
authenticator = None
try:
    # ... (code khởi tạo authenticator như cũ) ...
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
    authenticator.logout('Đăng xuất', 'sidebar')

    st.title("📊 Bảng điều khiển Admin - AI Đồng Hành Học Đường")
    st.markdown("---")

    # --- PHẦN TƯƠNG TÁC CSDL ---
    @st.cache_resource # Cache kết nối để tránh mở lại liên tục
    def connect_db():
        """Kết nối đến CSDL PostgreSQL."""
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
                     port=db_creds.get("port", 5432),
                     dbname=db_creds["dbname"],
                     user=db_creds["user"],
                     password=db_creds["password"],
                     sslmode=db_creds.get("sslmode", "require") # Quan trọng cho Neon
                 )
            else:
                st.error("Thiếu thông tin kết nối CSDL trong Streamlit Secrets.")
                return None
            print("Kết nối CSDL thành công!") # Ghi log ra console khi thành công
            return conn
        except psycopg2.OperationalError as e:
             # Lỗi cụ thể hơn khi không kết nối được server
             st.error(f"Lỗi kết nối CSDL: Không thể kết nối tới server. Kiểm tra host, port, network, SSL và thông tin xác thực.")
             print(f"Lỗi OperationalError kết nối DB: {e}") # Ghi log chi tiết
             return None
        except Exception as e:
            # Các lỗi khác (ví dụ: sai mật khẩu, sai tên db)
            st.error(f"Lỗi kết nối CSDL: {e}")
            print(f"Lỗi khác kết nối DB: {e}") # Ghi log chi tiết
            return None

    db_connection = connect_db()

    def fetch_dashboard_stats(conn):
        """Lấy các số liệu thống kê từ CSDL."""
        if conn is None:
            # Trả về giá trị lỗi/N/A nếu không có kết nối
            return {"weekly_chats": "N/A", "new_alerts": "N/A", "popular_topic": "N/A"}

        stats = {"weekly_chats": "N/A", "new_alerts": "N/A", "popular_topic": "N/A"} # Giá trị mặc định
        cursor = None
        try:
            cursor = conn.cursor() # Sử dụng cursor mặc định (trả về tuple)

            # Đếm cảnh báo mới
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Mới'")
            result_alerts = cursor.fetchone()
            stats["new_alerts"] = result_alerts[0] if result_alerts else 0

            # Đếm cuộc trò chuyện (Ví dụ - Cần bảng 'conversations' với cột 'start_time')
            # cursor.execute("SELECT COUNT(*) FROM conversations WHERE start_time >= NOW() - interval '7 day'")
            # result_chats = cursor.fetchone()
            # stats["weekly_chats"] = result_chats[0] if result_chats else 0
            stats["weekly_chats"] = "N/A" # Tạm thời

            # Lấy chủ đề nổi bật từ lý do cảnh báo
            cursor.execute("""
                SELECT reason, COUNT(*) as count
                FROM alerts
                GROUP BY reason
                ORDER BY count DESC
                LIMIT 1
            """)
            popular = cursor.fetchone()
            stats["popular_topic"] = popular[0] if popular else "Không có"

            print(f"Fetched stats: {stats}") # Log kết quả
            return stats

        except Exception as e:
            st.error(f"Lỗi truy vấn thống kê: {e}")
            print(f"Lỗi trong fetch_dashboard_stats: {e}")
            return stats # Trả về dict chứa lỗi/N/A
        finally:
             if cursor:
                 cursor.close()

    def fetch_alerts(conn, status_filter=None):
        """Lấy danh sách cảnh báo từ CSDL."""
        if conn is None:
            st.warning("Không có kết nối CSDL, sử dụng dữ liệu giả lập cho cảnh báo.")
            # --- Dữ liệu giả lập ---
            dummy_alerts_list = [
                 {"id": "dummy_1", "timestamp": datetime.datetime(2023, 10, 27, 10, 15), "reason": "Giả lập - Tự hại", "snippet": "...", "status": "Mới", "assignee": None, "priority": 1},
                 {"id": "dummy_2", "timestamp": datetime.datetime(2023, 10, 27, 9, 30), "reason": "Giả lập - Lo âu", "snippet": "...", "status": "Đang xử lý", "assignee": "Admin Demo", "priority": 2},
            ]
            df = pd.DataFrame(dummy_alerts_list)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            if status_filter and status_filter != "Tất cả":
                return df[df['status'] == status_filter].copy()
            return df.copy()
            # --- Kết thúc dữ liệu giả lập ---

        # Lấy dữ liệu thật
        print(f"Fetching alerts with filter: {status_filter}") # Log
        try:
            # **QUAN TRỌNG**: Đảm bảo tên cột khớp với CSDL của bạn
            query = "SELECT id, timestamp, reason, snippet, status, assignee, priority FROM alerts"
            params = []
            if status_filter and status_filter != "Tất cả":
                query += " WHERE status = %s"
                params.append(status_filter)
            query += " ORDER BY timestamp DESC"

            print(f"Executing query: {query} with params: {params}") # Log query
            df = pd.read_sql(query, conn, params=params)
            print(f"Fetched {len(df)} alerts from DB.") # Log số lượng

            # Chuyển đổi kiểu dữ liệu nếu cần (đặc biệt là timestamp)
            if not df.empty:
                if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                     df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Xử lý múi giờ nếu CSDL lưu UTC và bạn muốn hiển thị giờ địa phương
                # Ví dụ: df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Ho_Chi_Minh')

            return df

        except Exception as e:
            st.error(f"LỖI fetch_alerts: Không thể tải danh sách cảnh báo từ CSDL. Chi tiết: {e}")
            print(f"--- LỖI TRONG fetch_alerts ---")
            print(f"Query: {query}")
            print(f"Params: {params}")
            print(f"Lỗi: {e}")
            print(f"Loại lỗi: {type(e).__name__}")
            print(f"----------------------------")
            return pd.DataFrame() # Trả về DataFrame rỗng

    def update_alert_status_in_db(conn, alert_id, new_status, assignee):
        """Cập nhật trạng thái và người phụ trách của cảnh báo trong CSDL."""
        if conn is None:
            st.error("Không có kết nối CSDL, không thể cập nhật.")
            return False

        cursor = None
        try:
            cursor = conn.cursor()
            print(f"Attempting to update alert ID: {alert_id} to Status: {new_status}, Assignee: {assignee}") # Log
            # **QUAN TRỌNG**: Đảm bảo tên cột và bảng khớp
            cursor.execute(
                "UPDATE alerts SET status = %s, assignee = %s WHERE id = %s",
                (new_status, assignee, alert_id)
            )
            conn.commit() # !! LƯU THAY ĐỔI VÀO CSDL !!

            # Kiểm tra xem có dòng nào thực sự được cập nhật không
            if cursor.rowcount > 0:
                print(f"DB Update successful for alert ID {alert_id}. Rows affected: {cursor.rowcount}") # Log thành công
                return True
            else:
                # Không có dòng nào được cập nhật (có thể do ID không đúng)
                st.warning(f"Không tìm thấy cảnh báo ID {alert_id} để cập nhật hoặc trạng thái không thay đổi.")
                conn.rollback() # Không cần thiết nhưng rõ ràng
                return False

        except Exception as e:
            if conn:
                conn.rollback() # Hoàn tác nếu có lỗi
            st.error(f"Lỗi CSDL khi cập nhật cảnh báo ID {alert_id}: {e}")
            print(f"--- LỖI TRONG update_alert_status_in_db ---")
            print(f"Alert ID: {alert_id}, New Status: {new_status}, Assignee: {assignee}")
            print(f"Lỗi: {e}")
            print(f"Loại lỗi: {type(e).__name__}")
            print(f"------------------------------------")
            return False
        finally:
             if cursor:
                 cursor.close()

    def add_faq_to_db(conn, question, answer, category=None):
        """Thêm FAQ mới vào CSDL."""
        if conn is None:
            st.error("Không có kết nối CSDL, không thể thêm FAQ.")
            return False
        cursor = None
        try:
            cursor = conn.cursor()
            # **QUAN TRỌNG**: Đảm bảo tên bảng và cột khớp
            print(f"Adding FAQ: Q='{question[:30]}...', Cat='{category}'") # Log
            cursor.execute(
                "INSERT INTO knowledge_base (question, answer, category) VALUES (%s, %s, %s)",
                (question, answer, category)
            )
            conn.commit() # !! LƯU THAY ĐỔI VÀO CSDL !!
            print("FAQ added successfully to DB.") # Log thành công
            return True
        except Exception as e:
            if conn: conn.rollback()
            st.error(f"Lỗi CSDL khi thêm FAQ: {e}")
            print(f"--- LỖI TRONG add_faq_to_db ---")
            print(f"Question: {question[:50]}...")
            print(f"Category: {category}")
            print(f"Lỗi: {e}")
            print(f"Loại lỗi: {type(e).__name__}")
            print(f"---------------------------")
            return False
        finally:
            if cursor: cursor.close()

# ... (sau các hàm CSDL khác) ...

def fetch_chat_history(conn, session_id):
    """Lấy lịch sử chat cho một session_id cụ thể từ CSDL."""
    if conn is None or not session_id:
        st.warning("Yêu cầu Session ID để truy vấn lịch sử chat.")
        return pd.DataFrame() # Trả về DataFrame rỗng

    print(f"Fetching chat history for session: {session_id}") # Log
    try:
        # Lấy các cột cần thiết, sắp xếp theo thời gian
        query = """
            SELECT timestamp, sender, message_content, user_id -- Lấy user_id nếu cần
            FROM conversations
            WHERE session_id = %s
            ORDER BY timestamp ASC
        """
        df = pd.read_sql(query, conn, params=(session_id,))
        print(f"Fetched {len(df)} messages for session {session_id}.") # Log số lượng

        # Chuyển đổi kiểu dữ liệu nếu cần
        if not df.empty:
            if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                 df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Xử lý múi giờ nếu cần
            # Ví dụ: df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Ho_Chi_Minh')

        return df

    except Exception as e:
        st.error(f"LỖI fetch_chat_history cho session {session_id}: {e}")
        print(f"--- LỖI TRONG fetch_chat_history ---")
        print(f"Session ID: {session_id}")
        print(f"Lỗi: {e}")
        print(f"Loại lỗi: {type(e).__name__}")
        print(f"---------------------------------")
        return pd.DataFrame() # Trả về DataFrame rỗng
    # --- KẾT THÚC ĐỊNH NGHĨA HÀM CSDL ---

    # --- Kiểm tra kết nối CSDL ---
    if db_connection is None:
        # Hàm connect_db đã hiển thị lỗi, chỉ hiển thị cảnh báo chung
        st.warning("Không thể kết nối đến Cơ sở dữ liệu. Một số chức năng sẽ sử dụng dữ liệu giả lập hoặc bị hạn chế.")
        # Không dừng app, cho phép hiển thị phần không cần DB (nếu có)
    else:
        st.success("Đã kết nối Cơ sở dữ liệu thành công.") # Thêm thông báo thành công

    # --- Hiển thị Dashboard Tổng quan ---
    st.header("📈 Tổng quan Hoạt động")
    stats = fetch_dashboard_stats(db_connection) # Gọi hàm lấy stats thật
    col1, col2, col3 = st.columns(3)
    col1.metric("Cuộc trò chuyện (7 ngày)", stats.get("weekly_chats", "N/A"))
    col2.metric("Cảnh báo mới", stats.get("new_alerts", "N/A"))
    col3.metric("Chủ đề nổi bật", stats.get("popular_topic", "N/A"))

    st.markdown("---")

    # --- Quản lý Cảnh báo ---
    st.header("🚨 Quản lý Cảnh báo")
    alerts_df = fetch_alerts(db_connection) # Gọi hàm lấy alerts thật

    if not alerts_df.empty:
        st.info(f"Tìm thấy {len(alerts_df)} cảnh báo.") # Thông tin số lượng
        # Bộ lọc trạng thái
        # Lấy danh sách trạng thái từ dữ liệu thực tế hoặc định nghĩa trước
        # status_options = ["Tất cả"] + sorted(list(alerts_df['status'].unique()))
        status_options = ["Tất cả", "Mới", "Đang xử lý", "Đã giải quyết"] # Hoặc định nghĩa cứng nếu muốn thứ tự cụ thể
        selected_status = st.selectbox("Lọc theo trạng thái:", status_options)

        # Lọc DataFrame dựa trên lựa chọn
        if selected_status != "Tất cả":
            # Quan trọng: Đảm bảo alerts_df là DataFrame trước khi lọc
            if isinstance(alerts_df, pd.DataFrame):
                 display_df = alerts_df[alerts_df['status'] == selected_status].copy() # Thêm .copy()
            else:
                 display_df = pd.DataFrame() # Trả về df rỗng nếu alerts_df không hợp lệ
        else:
            display_df = alerts_df.copy() # Thêm .copy()

        # Hiển thị bảng cảnh báo
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.subheader("Xem và Cập nhật Cảnh báo")
         # Lấy ID từ DataFrame thực tế
        alert_id_options = [""] + (list(alerts_df['id'].astype(str).unique()) if isinstance(alerts_df, pd.DataFrame) and 'id' in alerts_df else [])
        selected_alert_id_str = st.selectbox("Chọn ID cảnh báo để xử lý:", alert_id_options)

        # Xử lý khi một ID được chọn
        if selected_alert_id_str and isinstance(alerts_df, pd.DataFrame):
            try:
                # Cố gắng tìm dòng tương ứng, chuyển đổi kiểu ID nếu cần (ví dụ nếu ID trong DB là số)
                # Giả sử ID trong DataFrame là kiểu dữ liệu gốc từ DB
                selected_data_series = alerts_df[alerts_df['id'].astype(str) == selected_alert_id_str].iloc[0]

                # Chuyển Series thành Dictionary để dễ truy cập
                selected_data = selected_data_series.to_dict()

                st.write(f"**Chi tiết cảnh báo ID:** `{selected_data.get('id', 'N/A')}`")
                # Định dạng timestamp đẹp hơn
                ts = selected_data.get('timestamp')
                ts_display = ts.strftime('%Y-%m-%d %H:%M:%S %Z') if pd.notna(ts) else "N/A"
                st.write(f"**Thời gian:** {ts_display}")
                st.write(f"**Lý do:** {selected_data.get('reason', 'N/A')}")
                st.write(f"**Trích đoạn:**")
                st.text_area("Snippet", selected_data.get('snippet', ''), height=100, disabled=True)
                st.write(f"**Độ ưu tiên:** {selected_data.get('priority', 'N/A')}") # Hiển thị priority


                # Form cập nhật
                with st.form(key=f"update_alert_{selected_alert_id_str}"):
                    st.write("**Cập nhật trạng thái và người phụ trách:**")
                    # Lấy danh sách status options đã định nghĩa ở trên
                    current_status = selected_data.get('status', status_options[1]) # Mặc định là 'Mới' nếu không có
                    try:
                        # Tìm index cẩn thận hơn
                        current_status_index = status_options.index(current_status) if current_status in status_options else 1
                    except ValueError:
                        current_status_index = 1 # Mặc định về 'Mới' nếu trạng thái hiện tại không có trong options

                    new_status = st.selectbox("Trạng thái mới:", options=status_options[1:], index=max(0, current_status_index - 1)) # Bỏ "Tất cả", điều chỉnh index
                    # Lấy assignee hiện tại, nếu là None/NaN thì dùng tên admin đang login
                    current_assignee = selected_data.get('assignee')
                    default_assignee = name if pd.isna(current_assignee) else current_assignee
                    assignee = st.text_input("Người phụ trách:", value=default_assignee)

                    submitted = st.form_submit_button("Lưu thay đổi")
                    if submitted:
                        # Lấy ID gốc (có thể là int hoặc string tùy DB) để truyền vào hàm update
                        original_alert_id = selected_data.get('id')
                        if original_alert_id is not None:
                            # Gọi hàm cập nhật CSDL thực tế
                            success = update_alert_status_in_db(db_connection, original_alert_id, new_status, assignee)
                            if success:
                                st.success(f"Đã gửi yêu cầu cập nhật cảnh báo {original_alert_id}!")
                                # Rerun để làm mới bảng dữ liệu
                                st.rerun() # Dùng hàm rerun chuẩn
                            # else: # Hàm update đã hiển thị lỗi
                            #    st.error(f"Có lỗi xảy ra khi cập nhật cảnh báo {original_alert_id}.")
                        else:
                            st.error("Không thể xác định ID cảnh báo để cập nhật.")

            except IndexError:
                 st.warning(f"Không tìm thấy dữ liệu chi tiết cho ID: {selected_alert_id_str}")
            except Exception as e:
                 st.error(f"Lỗi khi hiển thị chi tiết cảnh báo: {e}")
                 print(f"Lỗi hiển thị chi tiết cảnh báo {selected_alert_id_str}: {e}")


    elif db_connection is not None: # Chỉ hiển thị 'không có' nếu có kết nối DB nhưng fetch về rỗng
        st.info("Hiện không có cảnh báo nào trong cơ sở dữ liệu.")
    # Không hiển thị gì nếu chưa kết nối được DB

    st.markdown("---")

    # --- Quản lý Cơ sở Kiến thức ---
    st.header("📚 Quản lý Cơ sở Kiến thức")
    # (Cần thêm code để fetch và hiển thị danh sách FAQ hiện có)
    # Ví dụ:
    # st.subheader("Danh sách FAQ")
    # faq_df = fetch_faqs(db_connection) # Cần viết hàm fetch_faqs
    # if faq_df is not None and not faq_df.empty:
    #     st.dataframe(faq_df)
    # else:
    #     st.info("Chưa có FAQ nào.")

    with st.expander("Thêm câu hỏi thường gặp (FAQ) mới"):
        new_question = st.text_input("Câu hỏi:", key="faq_question")
        new_answer = st.text_area("Câu trả lời:", key="faq_answer")
        new_category = st.text_input("Chủ đề (Category):", key="faq_category") # Thêm input cho category
        if st.button("Thêm FAQ"):
            if new_question and new_answer:
                # --- Gọi hàm lưu FAQ vào CSDL ---
                success = add_faq_to_db(db_connection, new_question, new_answer, new_category) # Gọi hàm thật
                if success:
                    st.success("Đã thêm FAQ vào Cơ sở dữ liệu thành công!")
                    # Có thể thêm st.rerun() để làm mới danh sách FAQ nếu có hiển thị
                    # st.rerun()
                # Lỗi đã được hiển thị trong hàm add_faq_to_db
            else:
                st.warning("Vui lòng nhập cả câu hỏi và câu trả lời.")


    st.markdown("---")

    # --- Các phần khác (Placeholder) ---
    st.header("👤 Quản lý Người dùng Admin")
    st.info("Hiện tại quản lý người dùng qua file `config.yaml`.")

        # ... (sau phần Quản lý Cơ sở Kiến thức) ...

    st.markdown("---")

    # --- Xem lại Lịch sử Chat ---
    st.header("💬 Xem lại Lịch sử Chat")
    st.warning("⚠️ Tính năng này chỉ dành cho mục đích gỡ lỗi và điều tra sự cố an toàn. Truy cập phải được ghi log và tuân thủ quy định bảo mật.")

    # --- Cơ chế tìm kiếm/lọc đơn giản ---
    # Cách 1: Tìm theo Session ID (nếu bạn biết ID)
    search_session_id = st.text_input("Nhập Session ID để xem lịch sử chat:", key="chat_session_search")

    # Cách 2: Hoặc liên kết từ Bảng Cảnh báo (Nếu bạn đã lưu session_id trong bảng alerts)
    st.write("Hoặc chọn từ cảnh báo (nếu có Session ID liên kết):")
    # Lấy danh sách session_id từ các cảnh báo đã fetch (alerts_df)
    linked_session_ids = [""] # Thêm lựa chọn rỗng
    if 'alerts_df' in locals() and isinstance(alerts_df, pd.DataFrame) and 'chat_session_id' in alerts_df.columns:
         # Lấy các session_id không rỗng và duy nhất
         valid_sessions = alerts_df[pd.notna(alerts_df['chat_session_id'])]['chat_session_id'].unique()
         linked_session_ids.extend(list(valid_sessions))

    selected_linked_session = st.selectbox("Chọn Session ID từ cảnh báo:", options=linked_session_ids, key="chat_session_select")

    # Xác định session_id cần tìm
    session_id_to_fetch = None
    if search_session_id:
        session_id_to_fetch = search_session_id
    elif selected_linked_session:
        session_id_to_fetch = selected_linked_session

    # Nếu có session_id để tìm và có kết nối DB
    if session_id_to_fetch and db_connection:
        st.write(f"Đang tải lịch sử cho Session ID: `{session_id_to_fetch}`")
        chat_history_df = fetch_chat_history(db_connection, session_id_to_fetch)

        if not chat_history_df.empty:
            st.write(f"**Lịch sử chat:**")
            # Hiển thị dạng chat message mô phỏng
            for index, row in chat_history_df.iterrows():
                role = "user" if str(row.get('sender', '')).lower() == 'user' else "assistant"
                timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row.get('timestamp')) else ""
                with st.chat_message(role):
                     st.markdown(row.get('message_content', ''))
                     # Có thể thêm user_id (nếu được phép) và timestamp vào caption
                     st.caption(f"Sender: {row.get('sender', 'N/A')} | User: {row.get('user_id', 'N/A')} | Time: {timestamp_str}")
        elif db_connection: # Chỉ báo không tìm thấy nếu có kết nối DB
            st.info(f"Không tìm thấy lịch sử chat cho Session ID: {session_id_to_fetch}")
    elif (search_session_id or selected_linked_session) and not db_connection:
         st.error("Không thể tìm kiếm lịch sử chat do không có kết nối CSDL.")


    # --- KẾT THÚC NỘI DUNG CHÍNH CỦA TRANG ADMIN ---
    # --- KẾT THÚC NỘI DUNG CHÍNH CỦA TRANG ADMIN ---
