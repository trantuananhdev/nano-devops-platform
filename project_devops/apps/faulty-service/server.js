const express = require('express');
const app = express();
const port = process.env.PORT || 8080;

// Giả lập một Database local trong bộ nhớ
let userCache = {};
let requestLogs = [];

/**
 * BUG 1: Memory Leak ngầm (Hidden Leak)
 * Thay vì leak mảng khổng lồ ngay lập tức, ta sẽ lưu lại thông tin request
 * nhưng "quên" dọn dẹp hoặc giới hạn kích thước.
 * Càng gọi endpoint /status nhiều, RAM càng tăng dần.
 */
app.get('/status', (req, res) => {
  console.log('🚀 [CI/CD V5.0] Final Validation: The automated pipeline is rock solid!');
  const meta = {
    timestamp: new Date(),
    headers: req.headers,
    ua: req.get('User-Agent'),
    // Giả lập dữ liệu nặng được đính kèm vào mỗi log request
    payload: new Array(1000).fill("ghost-log-data-segment-" + Math.random())
  };
  requestLogs.push(meta); 
  
  res.json({ 
    status: 'online', 
    requestsHandled: requestLogs.length,
    memoryUsage: `${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)} MB`
  });
});

/**
 * BUG 2: Race Condition & Crash (Hard to smell)
 * Một lỗi không xảy ra ngay lập tức mà phụ thuộc vào việc xử lý bất đồng bộ không an toàn.
 */
let isProcessing = false;
app.get('/sync-data', async (req, res) => {
  if (isProcessing) {
    // Nếu có 2 request cùng lúc gọi vào đây, một cái sẽ gây crash do truy cập tài nguyên đang bị khóa
    console.error('🔥 [CRITICAL] Data Sync Conflict: Multiple concurrent processes detected!');
    console.error('Stack Trace: Error: ConcurrentModificationException at InternalState.sync');
    process.exit(1); 
  }

  isProcessing = true;
  console.log('🔄 Starting data synchronization...');
  
  // Giả lập một tác vụ nặng tốn 2 giây
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  isProcessing = false;
  console.log('✅ Sync complete.');
  res.json({ message: 'Data synchronized successfully.' });
});

app.get('/', (req, res) => {
  res.send(`
    <h1>Ghost Engineer Test Target: Faulty Service</h1>
    <p>Endpoints để test:</p>
    <ul>
      <li><code>/status</code> - Kiểm tra trạng thái (Gây rò rỉ RAM ngầm)</li>
      <li><code>/sync-data</code> - Đồng bộ dữ liệu (Gây Crash nếu gọi nhanh 2 lần liên tiếp)</li>
    </ul>
  `);
});

app.listen(port, () => {
  console.log(`🚀 Faulty Service v2 listening at http://localhost:${port}`);
  console.log(`🆔 Service PID: ${process.pid}`);
});
