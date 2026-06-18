const API_BASE = 'http://' + window.location.hostname + ':8000';
let testHistory = JSON.parse(localStorage.getItem('testHistory') || '[]');
let isRunning = false;
let lastServiceStatus = true; // 追蹤上次的服務狀態
let serviceCheckFailCount = 0; // 連續檢查失敗次數
const POLL_TIMEOUT_MS = 5 * 60 * 1000; // 5 分鐘輪詢上限

// Toast 通知系統
const Toast = {
    show(message, title = '通知', type = 'error', duration = 5000) {
        const container = document.getElementById('toastContainer');
        const toastId = 'toast-' + Date.now();

        const icons = {
            success: '✓',
            warning: '⚠️',
            error: '✗'
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.id = toastId;
        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || '📢'}</div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="Toast.close('${toastId}')">×</button>
        `;

        container.appendChild(toast);

        // 自動關閉
        if (duration > 0) {
            setTimeout(() => {
                Toast.close(toastId);
            }, duration);
        }

        return toastId;
    },

    close(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.classList.add('removing');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }
    },

    success(message, title = '成功') {
        return this.show(message, title, 'success');
    },

    warning(message, title = '警告') {
        return this.show(message, title, 'warning');
    },

    error(message, title = '錯誤') {
        return this.show(message, title, 'error');
    }
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    checkStatus();
    renderHistory();
    loadTraceSessions();

    // Event delegation for trace container (避免 XSS)
    document.getElementById('traceContainer').addEventListener('click', (e) => {
        const header = e.target.closest('.session-header');
        const viewBtn = e.target.closest('.btn-view-trace');

        if (header) {
            toggleTraceFiles(header.dataset.sessionId);
        } else if (viewBtn) {
            viewTrace(viewBtn.dataset.sessionId, viewBtn.dataset.traceName);
        }
    });
});

// 檢查狀態
async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();

        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');

        if (data.is_busy) {
            statusDot.className = 'status-dot busy';
            statusText.textContent = `執行中: ${data.current_test || '測試中'}`;
            isRunning = true;
        } else {
            statusDot.className = 'status-dot idle';
            statusText.textContent = '系統閒置中';
            isRunning = false;
        }

        document.getElementById('runBtn').disabled = isRunning;

        // 服務恢復正常
        if (!lastServiceStatus) {
            Toast.success('服務已恢復連接', '連接成功');
            lastServiceStatus = true;
        }
        serviceCheckFailCount = 0;

    } catch (error) {
        console.error('無法連接到後端服務:', error);
        serviceCheckFailCount++;

        // 只在第一次失敗或連續失敗3次時顯示 Toast
        if (lastServiceStatus || serviceCheckFailCount >= 3) {
            document.getElementById('statusText').textContent = '⚠️ 無法連接服務';
            Toast.error('服務無法連接，請檢查服務狀態', '未連接到服務', 8000);
            lastServiceStatus = false;
        }
    }
}

// 執行測試
async function runTest() {
    const testCase = document.getElementById('testCase').value;
    const env = document.getElementById('env').value;
    const site = document.getElementById('site').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const url = `${API_BASE}/api/tests/${testCase}`
    const payload = { env, site};
    if (username) payload.username = username;
    if (password) payload.password = password;

    document.getElementById('currentResult').innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>測試執行中，請稍候...</p>
        </div>
    `;

    document.getElementById('runBtn').disabled = true;
    isRunning = true;
    checkStatus();

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        // 測試已啟動，顯示提示訊息
        document.getElementById('currentResult').innerHTML = `
            <div class="result-panel">
                <div class="result-item" style="border-left-color: #f59e0b;">
                    <div class="result-header">
                        <strong>⏳ ${result.message}</strong>
                        <span class="result-badge" style="background: #fef3c7; color: #92400e;">執行中</span>
                    </div>
                    <div class="result-details">
                        <p>${result.hint}</p>
                        <p>測試執行中，請稍候片刻...</p>
                    </div>
                </div>
            </div>
        `;

        Toast.success('測試已啟動，請稍候片刻', '測試啟動');

        // 開始輪詢狀態
        pollTestStatus();

    } catch (error) {
        document.getElementById('currentResult').innerHTML = `
            <div class="result-item error">
                <div class="result-header">
                    <strong>執行錯誤</strong>
                    <span class="result-badge badge-error">ERROR</span>
                </div>
                <div class="result-details">
                    ${error.message || '無法連接到後端服務'}
                </div>
            </div>
        `;
        Toast.error(error.message || '無法連接到後端服務', '執行失敗');
    }
}

// 輪詢測試狀態
let pollInterval = null;
async function pollTestStatus() {
    if (pollInterval) clearInterval(pollInterval);

    const pollStartTime = Date.now();

    pollInterval = setInterval(async () => {
        // 超過 5 分鐘自動停止
        if (Date.now() - pollStartTime > POLL_TIMEOUT_MS) {
            clearInterval(pollInterval);
            isRunning = false;
            document.getElementById('runBtn').disabled = false;
            Toast.warning('測試執行時間過長，請手動確認狀態', '輪詢逾時');
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/status`);
            const data = await response.json();

            // 如果測試還在執行中，繼續等待
            if (data.is_busy) {
                return;
            }

            // 測試完成了
            clearInterval(pollInterval);
            isRunning = false;
            document.getElementById('runBtn').disabled = false;

            // 顯示測試結果
            if (!data.is_busy && data.latest !== null) {
                const result = data.latest.result;
                const testCase = document.getElementById('testCase').value;
                const env = document.getElementById('env').value;
                const site = document.getElementById('site').value;

                const historyItem = {
                    timestamp: new Date().toLocaleString('zh-TW'),
                    testCase,
                    env,
                    site,
                    result
                };
                testHistory.unshift(historyItem);
                if (testHistory.length > 20) testHistory.pop();
                localStorage.setItem('testHistory', JSON.stringify(testHistory));

                displayResult(result);
                renderHistory();

                // 顯示測試完成通知
                if (result.success) {
                    Toast.success('所有測試案例已通過', '測試完成');
                } else {
                    Toast.warning('部分測試案例未通過，請查看詳細報告', '測試完成');
                }

                // 重新載入 traces
                setTimeout(() => loadTraceSessions(), 3000);
            }

        } catch (error) {
            console.error('輪詢狀態失敗:', error);
            clearInterval(pollInterval);
            isRunning = false;
            document.getElementById('runBtn').disabled = false;
        }
    }, 2000); // 每 2 秒檢查一次
}

// 顯示結果
function displayResult(result) {
    const statusClass = result.success ? 'success' : 'error';
    const badgeClass = result.success ? 'badge-success' : 'badge-error';
    const statusText = result.success ? '✓ 通過' : '✗ 失敗';

    const links = [];
    if (result.html_report) {
        links.push(`<a href="${API_BASE}/api/reports/html" target="_blank">📊 HTML報告</a>`);
    }

    const summary = result.summary || {};
    const passed = summary.passed || 0;
    const failed = summary.failed || 0;
    const duration = result.duration || 0;

    document.getElementById('currentResult').innerHTML = `
        <div class="result-panel">
            <div class="result-item ${statusClass}">
                <div class="result-header">
                    <strong>${result.message || '測試完成'}</strong>
                    <span class="result-badge ${badgeClass}">${statusText}</span>
                </div>
                <div class="result-details">
                    <p>執行時間: ${duration} 秒</p>
                    <p>通過: ${passed} | 失敗: ${failed}</p>
                </div>
                ${links.length > 0 ? `<div class="result-links">${links.join('')}</div>` : ''}
            </div>
        </div>
    `;
}

// 渲染歷史記錄
function renderHistory() {
    const historyList = document.getElementById('historyList');

    if (testHistory.length === 0) {
        historyList.innerHTML = '<p style="text-align: center; color: #9ca3af; padding: 40px;">尚無測試記錄</p>';
        return;
    }

    historyList.innerHTML = testHistory.map((item, index) => {
        const statusIcon = item.result.success ? '✓' : '✗';
        const statusColor = item.result.success ? '#10b981' : '#ef4444';

        return `
            <div class="history-item" onclick="showHistoryDetail(${index})">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${item.testCase}</strong> - ${item.env}/${item.site}
                        <div class="history-time">${item.timestamp}</div>
                    </div>
                    <span style="color: ${statusColor}; font-size: 20px;">${statusIcon}</span>
                </div>
            </div>
        `;
    }).join('');
}

// 顯示歷史詳情
function showHistoryDetail(index) {
    const item = testHistory[index];
    displayResult(item.result);
}

// 清除結果
function clearResults() {
    document.getElementById('currentResult').innerHTML = '';
}

// 載入 Trace Sessions
async function loadTraceSessions() {
    const container = document.getElementById('traceContainer');

    try {
        const response = await fetch(`${API_BASE}/api/traces/sessions`);
        const sessions = await response.json();

        if (sessions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div style="font-size: 48px; margin-bottom: 15px;">📭</div>
                    <h3>目前沒有失敗測試的 Trace</h3>
                    <p>當測試失敗時，Trace 檔案會自動保存在這裡</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="trace-sessions">
                ${sessions.map(session => {
                    const safeSessionId = session.session_id.replace(/"/g, '&quot;');
                    return `
                    <div class="trace-session">
                        <div class="session-header" data-session-id="${safeSessionId}">
                            <span class="session-title">📅 ${session.session_id}</span>
                            <span>
                                <span class="session-count">${session.count || session.trace_count || 0} 個失敗測試</span>
                                <span class="session-toggle-icon">▶</span>
                            </span>
                        </div>
                        <div class="trace-files" id="traces-${safeSessionId}">
                            ${session.traces.map(trace => {
                                const safeName = trace.name.replace(/"/g, '&quot;');
                                const displayName = trace.test_name || trace.name;
                                return `
                                <div class="trace-file">
                                    <div>
                                        <div class="trace-name">🔴 ${displayName}</div>
                                        <div class="trace-size">${(trace.size / 1024).toFixed(2)} KB</div>
                                    </div>
                                    <button class="btn-view-trace"
                                        data-session-id="${safeSessionId}"
                                        data-trace-name="${safeName}">
                                        查看 Trace
                                    </button>
                                </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (error) {
        console.error('載入 traces 失敗:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 48px; margin-bottom: 15px;">⚠️</div>
                <h3>載入失敗</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// 切換 Trace 檔案列表
function toggleTraceFiles(sessionId) {
    const element = document.getElementById(`traces-${sessionId}`);
    const session = element?.closest('.trace-session');
    if (element) {
        element.classList.toggle('active');
        session?.classList.toggle('expanded');
    } else {
        console.error(`找不到 ID: traces-${sessionId}`);
    }
}

// 查看 Trace
function viewTrace(sessionId, traceName) {
    const traceUrl = `${API_BASE}/traces/${sessionId}/${traceName}`;
    const link = document.createElement('a');
    link.href = traceUrl;
    link.download = traceName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    Toast.success('Trace 檔案已開始下載', '下載中');
    setTimeout(() => {
        window.open('https://trace.playwright.dev/', '_blank');
        Toast.show('請將下載的 zip 檔案拖入新開啟的網頁查看', '查看提示', 'warning', 8000);
    }, 500);
}

// 定期檢查狀態 - 改為 10 秒一次
setInterval(checkStatus, 10000);

// 定期更新 traces
setInterval(loadTraceSessions, 30000);

// 查看 Allure
async function viewAllure() {
    try {
        const response = await fetch(`${API_BASE}/api/reports/allure`);
        if (response.ok) {
            const data = await response.json();
            window.open(`${API_BASE}${data.url}`, '_blank');
        } else {
            const err = await response.json();
            Toast.warning(err.detail || '報告未就緒');
        }
    } catch (error) {
        console.error('Allure 錯誤:', error);
        Toast.error('無法取得報告路徑');
    }
}
