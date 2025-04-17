# pages/🔑_Admin_Dashboard.py

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import os # Import os để kiểm tra đường dẫn và file

st.set_page_config(page_title="Admin Dashboard", layout="wide") # Có thể đặt ở đầu

# --- DEBUG: Kiểm tra việc đọc file config.yaml ---
st.subheader("Debug Information (Loading Config)") # Tiêu đề cho dễ thấy
config_path = 'config.yaml' # Đảm bảo tên file và đường dẫn là chính xác so với vị trí file này

st.write(f"DEBUG: Thư mục làm việc hiện tại (cwd): `{os.getcwd()}`")
st.write(f"DEBUG: Kiểm tra tồn tại '{config_path}': `{os.path.exists(config_path)}`")

config = None # Khởi tạo config là None để xử lý nếu không đọc được file
try:
    if os.path.exists(config_path):
        with open(config_path) as file:
            config = yaml.load(file, Loader=SafeLoader)
            st.success(f"DEBUG: Đã tải file '{config_path}' thành công.")
            # In ra cấu trúc để chắc chắn
            st.write("DEBUG: Nội dung config đã tải:")
            st.json(config if config else "Config is None or Empty after loading")
    else:
        st.error(f"DEBUG Lỗi: Không tìm thấy file cấu hình tại đường dẫn '{config_path}' từ thư mục làm việc hiện tại.")
        st.stop() # Dừng nếu không tìm thấy file

except Exception as e:
    st.error(f"DEBUG Lỗi: Lỗi khi đọc hoặc phân tích file '{config_path}':")
    st.exception(e) # In ra traceback của lỗi YAML/IO
    st.stop() # Dừng nếu có lỗi đọc/phân tích

# Kiểm tra xem config có được tải đúng không trước khi tiếp tục
if not config:
    st.error("DEBUG Lỗi: Biến 'config' trống hoặc None sau khi cố gắng tải. Không thể tiếp tục.")
    st.stop()
# --- KẾT THÚC PHẦN DEBUG CONFIG ---


# --- Tiếp tục với phần còn lại của code ---

# --- Lấy Cookie Key từ Secrets ---
try:
    # Kiểm tra xem st.secrets có tồn tại mục 'cookie' và key 'key' không
    if 'cookie' in st.secrets and 'key' in st.secrets['cookie']:
        cookie_key = st.secrets["cookie"]["key"]
        if not cookie_key or len(cookie_key) < 32:
             raise ValueError("Cookie key không hợp lệ trong secrets (rỗng hoặc quá ngắn).")
        st.success("DEBUG: Đã lấy cookie_key từ secrets.")
        # Tạm thời in ra để kiểm tra (nên xóa sau)
        # st.write(f"DEBUG: Cookie Key Value: {cookie_key}")
        # st.write(f"DEBUG: Cookie Key Type: {type(cookie_key)}")
    else:
        raise KeyError("Không tìm thấy cấu trúc [cookie][key] trong Streamlit Secrets.")

except (KeyError, TypeError, ValueError) as e:
     st.error(f"DEBUG Lỗi cấu hình Cookie Key trong Streamlit Secrets: {e}")
     st.warning("Vui lòng kiểm tra lại cấu hình Secrets trên Streamlit Cloud. Cần có [cookie] và bên trong có 'key' với giá trị hợp lệ.")
     st.stop()


# --- Khởi tạo đối tượng Authenticator ---
# Kiểm tra các khóa cần thiết trong config trước khi khởi tạo
required_keys = ['credentials', 'cookie']
if not all(key in config for key in required_keys):
    st.error(f"DEBUG Lỗi: File config.yaml thiếu các khóa cần thiết: {required_keys}. Nội dung hiện tại: {config}")
    st.stop()
if 'name' not in config.get('cookie', {}) or 'expiry_days' not in config.get('cookie', {}):
     st.error(f"DEBUG Lỗi: Mục 'cookie' trong config.yaml thiếu 'name' hoặc 'expiry_days'.")
     st.stop()
if 'usernames' not in config.get('credentials', {}):
    st.error(f"DEBUG Lỗi: Mục 'credentials' trong config.yaml thiếu 'usernames'.")
    st.stop()

try:
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        cookie_key,
        config['cookie']['expiry_days']
    )
    st.success("DEBUG: Khởi tạo Authenticator thành công.")
except Exception as e:
    st.error("DEBUG Lỗi: Lỗi xảy ra trong quá trình khởi tạo stauth.Authenticate:")
    st.exception(e) # In traceback của lỗi khởi tạo
    st.stop()


# --- Hiển thị Form Đăng nhập ---
try:
    name, authentication_status, username = authenticator.login('main')
    st.success("DEBUG: Gọi authenticator.login('main') thành công.")
except Exception as e:
    st.error("DEBUG Lỗi: Lỗi xảy ra trong quá trình gọi authenticator.login('main'):")
    st.exception(e) # In traceback của lỗi khi gọi login
    st.stop()

# --- Kiểm tra Trạng thái Đăng nhập ---
# (Phần code còn lại giữ nguyên...)
if authentication_status is False:
    st.error('Tên đăng nhập/mật khẩu không chính xác')
    st.stop()
elif authentication_status is None:
    st.warning('Vui lòng nhập tên đăng nhập và mật khẩu')
    st.stop()
elif authentication_status:
    st.sidebar.success(f"Xin chào *{name}*")
    authenticator.logout('Logout', 'sidebar')
    # ... (Nội dung trang admin khi đã đăng nhập) ...
    st.title("📊 Bảng điều khiển Admin - AI Đồng Hành Học Đường")
    st.write(f"Chào mừng *{name}* đến trang quản trị!")
    # ... (phần hiển thị dữ liệu và các thành phần khác) ...
