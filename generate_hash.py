import streamlit_authenticator as stauth

# Nhập mật khẩu bạn muốn sử dụng cho tài khoản admin
plain_password = "Tuananh85!" # <<< THAY BẰNG MẬT KHẨU CỦA BẠN

hashed_password = stauth.Hasher([plain_password]).generate()
print(f"Mật khẩu của bạn là: {plain_password}")
print(f"Hash tương ứng (dùng trong config.yaml): {hashed_password[0]}")
