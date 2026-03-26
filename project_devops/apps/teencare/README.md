# TeenCare — Hệ thống Quản lý Học tập (LMS) tích hợp AI Insight

Dự án TeenCare là một nền tảng mini-LMS được thiết kế để quản lý thông tin học sinh, phụ huynh, lớp học và đặc biệt là tích hợp AI để phân tích nội dung buổi học (Session Insight).

## � Hướng dẫn Cài đặt Môi trường (Setup Guide)

Để đảm bảo dự án chạy "sure kèo" trên mọi máy tính (Windows hoặc macOS), chúng ta sử dụng **Vagrant** để tạo một môi trường máy ảo đồng nhất.

### 1. Yêu cầu chung (Prerequisites)
Bạn cần cài đặt các công cụ sau trước khi bắt đầu:
- **Vagrant**: [Tải tại đây](https://www.vagrantup.com/downloads)
- **VirtualBox** (Phổ biến nhất) hoặc **VMware**: [Tải VirtualBox](https://www.virtualbox.org/wiki/Downloads)

---

### 2. Hướng dẫn chi tiết cho từng Hệ điều hành

#### **A. Đối với Windows (Sử dụng PowerShell hoặc CMD)**
1.  **Cài đặt**: Tải file `.msi` của Vagrant và VirtualBox rồi cài đặt như phần mềm bình thường.
2.  **Bật Virtualization**: Đảm bảo BIOS của bạn đã bật "Intel VT-x" hoặc "AMD-V".
3.  **Clone dự án**:
    ```bash
    git clone <url-du-an>
    cd nano-project-devops
    ```
4.  **Khởi tạo máy ảo**:
    ```powershell
    vagrant up
    ```
5.  **Truy cập vào máy ảo**:
    ```powershell
    vagrant ssh
    ```

#### **B. Đối với macOS (Sử dụng Terminal)**
1.  **Cài đặt qua Homebrew** (Khuyên dùng):
    ```bash
    brew install --cask vagrant virtualbox
    ```
2.  **Cấp quyền**: macOS có thể yêu cầu bạn cấp quyền cho VirtualBox trong `System Settings > Security & Privacy`.
3.  **Khởi tạo máy ảo**:
    ```bash
    cd nano-project-devops
    vagrant up
    ```
4.  **Nếu dùng chip Apple Silicon (M1/M2/M3)**: 
    - VirtualBox hỗ trợ hạn chế, bạn nên sử dụng **VMware Fusion** (miễn phí cho cá nhân) kèm theo plugin:
    ```bash
    vagrant plugin install vagrant-vmware-desktop
    ```

---

#### **C. Chạy chế độ Production-Like (Mô phỏng Production thực tế)**
Nếu bạn muốn máy ảo chạy độc lập, không phụ thuộc vào thư mục code đang sửa (Immutable Infrastructure), hãy sử dụng lệnh sau:

- **Windows (PowerShell)**:
  ```powershell
  $env:COPY_PROJECT_DEVOPS="1"; vagrant up
  ```
- **Windows (CMD)**:
  ```cmd
  set COPY_PROJECT_DEVOPS=1 && vagrant up
  ```
- **macOS / Linux**:
  ```bash
  COPY_PROJECT_DEVOPS=1 vagrant up
  ```
*Lưu ý: Ở chế độ này, Vagrant sẽ copy toàn bộ code vào bên trong máy ảo thay vì mount thư mục. Mọi thay đổi code ở máy thật sẽ không tự cập nhật vào máy ảo cho đến khi bạn chạy lại lệnh provision.*

---

### 3. Sau khi máy ảo đã chạy
Khi đã `vagrant ssh` thành công vào bên trong máy ảo, bạn thực hiện các bước ở mục **Quick Start** phía dưới để chạy dự án.

---

## �� Hướng dẫn Bắt đầu nhanh (Quick Start)

### 1. Khởi động với Docker
Dự án đã được tích hợp sẵn vào hệ thống DevOps. Để khởi chạy toàn bộ Backend (FastAPI) và Frontend (React), hãy chạy lệnh:

```bash
# Di chuyển tới thư mục teencare
cd project_devops/apps/teencare

# Khởi chạy container
./scripts/lms_docker_up.sh
```

### 2. Khởi tạo dữ liệu mẫu (Seed Data)
Để có dữ liệu để test ngay lập tức (bao gồm 2 phụ huynh, 3 học sinh, 3 lớp học và 3 gói học), hãy chạy lệnh sau:

```bash
docker exec -it platform-teencare-lms-api python scripts/seed.py
```

### 3. Truy cập hệ thống
- **Giao diện Web**: `http://localhost:5173` (Hoặc Public IP của máy ảo)
- **Tài liệu API (Swagger)**: `http://localhost:8008/docs`
- **Hướng dẫn Test Postman**: Xem chi tiết tại [API_TEST_GUIDE.md](./API_TEST_GUIDE.md)

---

## 🛠 Các tính năng chính và Hướng dẫn sử dụng

### 1. Quản lý Phụ huynh & Học sinh
- Sử dụng Form trên giao diện Web để tạo mới **Parent**.
- Sau đó tạo **Student** và chọn Parent tương ứng. Thông tin này sẽ được lưu trữ đồng nhất giữa FE và BE.

### 2. Quản lý Lớp học & Đăng ký
- Xem lịch học theo tuần tại bảng **"Classes by Weekday"**.
- Đăng ký học sinh vào lớp thông qua form **"Register Student To Class"**.
- **Lưu ý các ràng buộc nghiệp vụ (Business Rules)**:
    - **Sĩ số**: Không thể đăng ký nếu lớp đã đạt `max_students`.
    - **Trùng lịch**: Hệ thống sẽ báo lỗi nếu học sinh đã có lớp khác vào cùng khung giờ trong cùng ngày.
    - **Gói học**: Chỉ được đăng ký nếu học sinh có gói học còn hạn (`end_date`) và còn buổi (`used_sessions < total_sessions`).

### 3. Chính sách Hủy lịch (Refund Policy)
- Khi xóa một đăng ký lớp học (`DELETE /api/registrations/{id}`):
    - **Trước > 24h**: Hệ thống tự động hoàn lại 1 buổi vào gói học (`used_sessions` giảm 1).
    - **Trong vòng < 24h**: Xóa đăng ký nhưng **không hoàn buổi**.

### 4. AI Session Insight (Phân tích buổi học)
Đây là tính năng cốt lõi giúp tạo ra Insight tin cậy cho phụ huynh sau mỗi buổi học:
- **Nhập text**: Dán transcript nội dung buổi học vào textarea trên Web và nhấn "Generate Insight".
- **Import file**: Nhấn chọn file `.txt` chứa nội dung buổi học để hệ thống tự động xử lý.
- **Kết quả**: AI sẽ phân tích và trả về JSON bao gồm: `insight_json`, `risk_level` (mức độ rủi ro), `confidence` (độ tin cậy), và các hành động (actions) cụ thể cho phụ huynh.

---

## 📊 Cấu trúc Cơ sở dữ liệu (Schema)

Hệ thống sử dụng SQLite (mặc định trong container) với các bảng chính:
- `parents`: Lưu thông tin liên lạc phụ huynh.
- `students`: Thông tin học sinh và liên kết tới `parent_id`.
- `classes`: Thông tin lớp học, môn học, giáo viên và khung giờ.
- `class_registrations`: Lưu vết đăng ký học sinh vào lớp kèm thời gian học.
- `subscriptions`: Quản lý gói học, tổng số buổi và số buổi đã dùng.
- `sessions`: Lưu trữ transcript và kết quả phân tích từ AI.

---

## 🏗 Cấu trúc Thư mục Project
- `lms_api/`: Backend FastAPI, xử lý logic nghiệp vụ và Database.
- `lms_web/`: Frontend React (Vite), giao diện người dùng.
- `src/teencare_ai/`: Core logic xử lý AI pipeline (Gemini/LLM).
- `scripts/`: Các script hỗ trợ build/run nhanh với Docker.

---

## 📝 Ghi chú cho Nhà phát triển
- Backend hỗ trợ CORS `*` để thuận tiện cho việc test local và qua IP Public.
- Frontend sử dụng biến môi trường `VITE_API_BASE_URL` để kết nối tới API.
- Để xem log của hệ thống: `docker logs -f platform-teencare-lms-api`.
