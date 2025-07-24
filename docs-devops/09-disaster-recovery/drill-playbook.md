# Disaster Recovery Drill Playbook - Nano DevOps Platform

**Last Updated**: 2026-03-03  
**Scope**: Disaster Recovery (DR) drills for a single-node, 6GB Nano DevOps Platform.

---

## 1. Purpose

Disaster Recovery drills (DR drills) biến **backup & restore strategy** thành **bài tập thực tế có đo lường**, để:

- Kiểm chứng RTO < 1h, RPO < 24h trong `backup-restore-strategy.md`.
- Đảm bảo runbook backup/restore thực sự dùng được trong tình huống sự cố.
- Tạo thói quen **DR game day** định kỳ (quý / nửa năm).

Đây là playbook **documentation-only** – không thay đổi kiến trúc hay script, chỉ hướng dẫn **cách chạy drill** dựa trên:

- `docs-devops/09-disaster-recovery/backup-restore-strategy.md`
- `docs-devops/10-runbook/backup-restore.md`

---

## 2. Roles & Responsibilities

- **DR Drill Coordinator**:
  - Lên lịch drill, define scope, thông báo liên quan.
  - Đảm bảo có môi trường an toàn (ưu tiên staging / lab).
  - Thu thập và lưu kết quả (RTO, RPO, issues).

- **Operator / Executor**:
  - Chạy các bước trong runbook và playbook này.
  - Ghi lại timestamps, lệnh đã chạy, quan sát thực tế.

- **Observer / Recorder (optional)**:
  - Ghi lại timeline, quyết định quan trọng, incident log.

---

## 3. Pre‑Drill Checklist (Common)

Trước bất kỳ drill nào:

- [ ] Drill chạy trên **môi trường non‑production** (ưu tiên).
- [ ] Có backup mới (< 24h) cho PostgreSQL & Redis.
- [ ] Đã thông báo cho những người liên quan (team DevOps / backend).
- [ ] Đã confirm đủ tài nguyên (disk, RAM) cho restore.
- [ ] Đã nắm rõ các scripts & runbooks:
  - `backup-restore-strategy.md`
  - `backup-restore.md`
- [ ] Có nơi lưu kết quả drill (ví dụ: wiki / repo docs / ticket).

---

## 4. Scenario A – PostgreSQL Data Loss Drill

**Mục tiêu**: Chứng minh có thể khôi phục PostgreSQL từ backup trong **< 1h** và dữ liệu không cũ hơn **24h**.

### 4.1 Setup & Safety

- Drill này nên chạy ở:
  - Staging / lab VM với data gần giống production.
  - Hoặc snapshot VM trước khi drill (nếu cần).

Không nên xoá dữ liệu production trực tiếp.

### 4.2 High‑Level Flow

```text
1) Xác nhận backup PostgreSQL gần nhất
2) Mô phỏng sự cố (mất dữ liệu / hỏng DB trên môi trường drill)
3) Thực hiện restore theo runbook
4) Đo và ghi nhận RTO, RPO
5) Xác nhận ứng dụng hoạt động lại bình thường
6) Ghi lại kết quả và lessons learned
```

### 4.3 Drill Steps (Chi Tiết)

1. **Record Start Time**
   - Ghi lại `DR_DRILL_ID` (ví dụ: `2026-03-03-pg-loss-drill-01`).
   - `T_start = now()`.

2. **Verify Latest Backups**
   - Theo `backup-restore.md`:
     - Liệt kê file `postgres_*.sql.gz` mới nhất.
     - Đảm bảo timestamp < 24h.

3. **Simulate Failure (On Drill Environment)**
   - Ví dụ (tùy môi trường / policy):
     - Drop database test / truncate critical tables.
     - Hoặc tạo một DB trống để restore vào.

4. **Execute Restore Procedure**
   - Làm theo **PostgreSQL Restore** trong `backup-restore.md`:
     - Dừng services phụ thuộc (data-api, user-api).
     - Restore từ file backup đã chọn.
     - Khởi động lại services.

5. **Functional Verification**
   - Chạy các bước verify trong runbook:
     - Kiểm tra DB schema / số bảng.
     - Gọi health endpoints `data-api`, `user-api`.
     - Chạy 1–2 luồng business quan trọng (nếu có script/guide).

6. **Measure RTO / RPO**
   - `T_end = now()`.
   - **RTO** = `T_end - T_start`.
   - **RPO** = tuổi của backup tại thời điểm restore (thời gian từ thời điểm backup tới lúc xảy ra sự cố giả lập).

7. **Record Results**
   - Ghi vào log drill (see section 6 – Recording Template).

---

## 5. Scenario B – Redis Data Loss Drill

**Mục tiêu**: Chứng minh có thể khôi phục Redis cache từ backup mà không phá vỡ ứng dụng.

### 5.1 High‑Level Flow

```text
1) Xác nhận backup Redis gần nhất
2) Mô phỏng mất dữ liệu Redis
3) Khôi phục từ backup theo runbook
4) Xác nhận ứng dụng vẫn hoạt động và xử lý cache đúng
```

### 5.2 Drill Steps

1. **Record Start Time**
   - `DR_DRILL_ID` (ví dụ: `2026-03-03-redis-loss-drill-01`).
   - `T_start = now()`.

2. **Verify Latest Backups**
   - Theo `backup-restore.md`:
     - Kiểm tra `redis_*.rdb.gz` mới nhất.

3. **Simulate Failure**
   - Trên môi trường drill:
     - Dừng container Redis.
     - Xoá hoặc rename file `dump.rdb` trong volume (sau khi backup bảo vệ).

4. **Execute Restore**
   - Thực hiện **Redis Restore** trong `backup-restore.md`:
     - Giải nén file backup vào data dir của Redis.
     - Set lại permission.
     - Khởi động lại Redis.

5. **Functional Verification**
   - Xác nhận Redis lên lại:
     - `redis-cli PING`
     - `DBSIZE` phù hợp / không 0 (nếu kỳ vọng).
   - Verify 1–2 luồng ứng dụng phụ thuộc Redis (nếu có).

6. **Measure RTO / RPO**
   - `T_end = now()`.
   - Tương tự Scenario A.

7. **Record Results**

---

## 6. Drill Recording Template

Khi chạy drill, tạo một entry (có thể trong wiki, docs, hoặc file log riêng):

```markdown
## [DR_DRILL_ID] - [Scenario A | Scenario B] - [Date]

**Environment**: [staging/lab/prod-like]  
**Coordinator**: [name]  
**Operators**: [names]  

### Scope
- Scenario: [PostgreSQL data loss / Redis data loss]
- Affected services: [list]

### Timeline
- Start time: [T_start]
- End time: [T_end]
- RTO: [duration]
- Backup timestamp: [backup_time]
- RPO: [T_start - backup_time]

### Steps Executed
- [ ] Verified latest backup
- [ ] Simulated failure
- [ ] Executed restore procedure
- [ ] Verified application behaviour

### Outcome
- Status: ✅ SUCCESS / ⚠️ PARTIAL / ❌ FAILED
- Data correctness: [OK / Issues]
- User impact (if any): [description]

### Issues & Follow-ups
- Issues observed:
  - [ ]
- Improvements:
  - [ ]

### Next Actions
- [ ] Update runbooks/strategy if needed
- [ ] Schedule next drill
```

---

## 7. Scheduling & Cadence

Khuyến nghị:

- **Tối thiểu 1–2 drill mỗi năm**, luân phiên:
  - Scenario A (PostgreSQL).
  - Scenario B (Redis).
- Có thể gom drill vào **“Game Day”**:
  - Kết hợp với chaos / failure simulation khác (tắt service, hạn chế tài nguyên, v.v.).

---

## 8. Links & Related Documents

- Backup Strategy: `docs-devops/09-disaster-recovery/backup-restore-strategy.md`
- Backup Automation: `docs-devops/09-disaster-recovery/backup-automation.md`
- Backup/Restore Runbook: `docs-devops/10-runbook/backup-restore.md`
- Incident Response: `docs-devops/10-runbook/incident-response.md` (nếu có)

