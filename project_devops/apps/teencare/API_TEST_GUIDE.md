# TeenCare LMS API - Test Guide (Localhost Forwarded)

Hướng dẫn này giúp bạn test API của TeenCare bằng cách sử dụng các cổng đã được forward trực tiếp từ máy ảo Vagrant ra máy thật (`localhost`).

---

## 1. Thiết lập & Khởi động (Chế độ "Lười")

Do domain chưa được xử lý, chúng ta sẽ truy cập thông qua `localhost` và các cổng đã forward trong [Vagrantfile](file:///c:/TA-work/nano-project-devops/Vagrantfile#L29-33).

### 1.1 Các Cổng Truy cập (Forwarded Ports)
- **LMS API**: `http://localhost:8008`
- **LMS Web**: `http://localhost:5173`
- **AI Dashboard**: `http://localhost:8501`

### 1.2 Khởi động & Seed dữ liệu (One-liner)
Sử dụng SSH key để thực thi lệnh từ máy thật (Sử dụng `sh` để chạy script, đảm bảo chạy được ngay cả khi chưa cấp quyền thực thi):

```bash
# Windows (PowerShell)
ssh -i ./.ssh/prod_key platform_admin@192.168.157.10 "cd /opt/platform/src/nano-project-devops/project_devops/apps/teencare && sh scripts/lms_docker_up.sh && docker exec platform-teencare-lms-api python scripts/seed.py"

# macOS / Linux
ssh -i ./.ssh/prod_key platform_admin@192.168.157.10 'cd /opt/platform/src/nano-project-devops/project_devops/apps/teencare && sh scripts/lms_docker_up.sh && docker exec platform-teencare-lms-api python scripts/seed.py'
```
*(Lưu ý: Tôi đã cập nhật Vagrantfile để tự động cấp quyền cho toàn bộ file .sh trong tương lai. Nếu lệnh trên vẫn lỗi, hãy chạy `vagrant provision` để đồng bộ lại).*
*(Thay `192.168.157.10` bằng IP thực tế của máy ảo nếu khác)*

---

## 2. Truy cập API

**Base URL**: `http://localhost:8008`

---

## 3. Postman Collection (Import & Chạy ngay)

Bạn có thể sử dụng bộ Collection đã được tôi tạo sẵn để Import trực tiếp vào Postman mà không cần copy-paste thủ công từng đoạn JSON:

### 3.1 Cách Import file nhanh nhất
1. Tải hoặc mở file [teencare_postman_collection.json](./teencare_postman_collection.json) trong thư mục dự án.
2. Mở Postman -> Nhấn nút **Import** (ở góc trên bên trái).
3. Kéo thả file này vào hoặc chọn file từ máy tính của bạn.
4. Nhấn **Import** để hoàn tất.

### 3.2 Mẹo về Base URL
- Tôi đã cài đặt sẵn biến `base_url` bên trong Collection này với giá trị mặc định là `http://localhost:8008`.
- Sau khi Import, bạn **không cần sửa thủ công** từng API. 
- Nếu muốn đổi Base URL (ví dụ dùng IP khác), bạn chỉ cần: Click vào tên Collection **"TeenCare LMS..."** -> Chọn tab **Variables** -> Sửa giá trị ở cột **Initial Value** của biến `base_url` -> Nhấn **Save**.

### 3.3 Nội dung Collection JSON (Dự phòng)
Nếu bạn không muốn tải file, có thể copy đoạn JSON dưới đây và lưu thành file `.json` để Import:

```json
{
	"info": {
		"name": "TeenCare LMS (Localhost Forwarded)",
		"schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
	},
	"item": [
		{
			"name": "System",
			"item": [
				{
					"name": "Health Check",
					"request": {
						"method": "GET",
						"url": { "raw": "{{base_url}}/health" }
					}
				}
			]
		},
		{
			"name": "Parents",
			"item": [
				{
					"name": "List All Parents",
					"request": {
						"method": "GET",
						"url": { "raw": "{{base_url}}/api/parents" }
					}
				},
				{
					"name": "Create Parent",
					"request": {
						"method": "POST",
						"body": {
							"mode": "raw",
							"raw": "{\n  \"name\": \"Nguyễn Văn A\",\n  \"phone\": \"0912345678\",\n  \"email\": \"vana@example.com\"\n}",
							"options": { "raw": { "language": "json" } }
						},
						"url": { "raw": "{{base_url}}/api/parents" }
					}
				}
			]
		},
		{
			"name": "Registrations",
			"item": [
				{
					"name": "Register Student to Class",
					"request": {
						"method": "POST",
						"body": {
							"mode": "raw",
							"raw": "{\n  \"student_id\": 1\n}",
							"options": { "raw": { "language": "json" } }
						},
						"url": { "raw": "{{base_url}}/api/classes/1/register" }
					}
				},
				{
					"name": "Cancel Registration (Refund Rule)",
					"request": {
						"method": "DELETE",
						"url": { "raw": "{{base_url}}/api/registrations/1" }
					}
				}
			]
		},
		{
			"name": "AI Session Insights",
			"item": [
				{
					"name": "Generate Insight from Text",
					"request": {
						"method": "POST",
						"body": {
							"mode": "raw",
							"raw": "{\n  \"student_id\": 1,\n  \"class_id\": 1,\n  \"raw_transcript\": \"Mentor: Chào em, hôm nay chúng ta học về giải phương trình bậc 2... Student: Dạ em hiểu rồi ạ.\"\n}",
							"options": { "raw": { "language": "json" } }
						},
						"url": { "raw": "{{base_url}}/api/sessions" }
					}
				}
			]
		}
	],
	"variable": [
		{
			"key": "base_url",
			"value": "http://localhost:8008",
			"type": "string"
		}
	]
}
```

---

## 5. Automated Test Script (PowerShell)

Nếu bạn muốn test tự động toàn bộ luồng nghiệp vụ trên Windows, hãy sử dụng script PowerShell sau. Script này sẽ tự động tạo dữ liệu, đăng ký lớp, kiểm tra lỗi hết buổi học và gọi AI Insight.

### 5.1 Cách chạy
1. Đảm bảo máy ảo Vagrant đang chạy.
2. Mở PowerShell trên máy thật.
3. Di chuyển tới thư mục project và chạy lệnh:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_api.ps1
```

### 5.2 Nội dung Script và Output mong đợi
Script thực hiện các bước sau:
1. **Health Check**: Kiểm tra API có sống không.
2. **Create Data**: Tạo Parent & Student mới để test độc lập.
3. **Subscription**: Tạo gói học chỉ có 2 buổi.
4. **Logic Register**: 
   - Đăng ký 2 lần thành công.
   - Đăng ký lần thứ 3 -> **Báo lỗi "Subscription has no remaining sessions"**.
5. **AI Insight**: Gửi transcript mẫu và nhận kết quả phân tích.

**Ví dụ Output mong đợi:**
```text
=== KIỂM TRA TRẠNG THÁI HỆ THỐNG ===
Health Check: ok

=== 1. TẠO PHỤ HUYNH & HỌC SINH ===
Đã tạo Parent ID: 10
Đã tạo Student ID: 15

=== 2. TẠO GÓI HỌC (SUBSCRIPTION) ===
Đã tạo Gói học cho Student 15. Tổng: 2 buổi.

=== 3. KIỂM TRA LOGIC ĐĂNG KÝ LỚP ===
Đăng ký buổi 1 (Success)...
Kết quả: Success (ID: 20)
Đăng ký buổi 2 (Success)...
Kết quả: Success (ID: 21)
Đăng ký buổi 3 (Expect Error: Hết lượt học)...
Output Error: {"detail":"Subscription has no remaining sessions"}

=== 4. KIỂM TRA AI SESSION INSIGHT ===
Đã tạo Insight ID: 5
Risk Level: LOW
Confidence: HIGH
```

