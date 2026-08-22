def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="ko" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ladypolo AI 비서 관리자 대시보드</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#fff1f2',
                            500: '#f43f5e',
                            600: '#e11d48',
                            700: '#be123c',
                        },
                        dark: {
                            900: '#0f172a',
                            800: '#1e293b',
                            700: '#334155',
                        }
                    }
                }
            }
        }
    </script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Pretendard', sans-serif; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">

    <!-- 1. LOGIN SCREEN -->
    <div id="loginSection" class="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-950 via-slate-900 to-rose-950/30">
        <div class="max-w-md w-full bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-3xl p-8 shadow-2xl shadow-rose-950/20">
            <div class="text-center mb-8">
                <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-500 mb-4 shadow-inner">
                    <i data-lucide="bot" class="w-10 h-10"></i>
                </div>
                <h1 class="text-2xl font-bold text-white tracking-tight">ladypolo AI 비서</h1>
                <p class="text-slate-400 text-sm mt-1">통합 관리자 설정 & 모니터링 포털</p>
            </div>

            <form id="loginForm" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">관리자 암호</label>
                    <div class="relative">
                        <i data-lucide="lock" class="w-5 h-5 absolute left-3.5 top-3 text-slate-500"></i>
                        <input type="password" id="adminPassword" required placeholder="암호를 입력하세요"
                            class="w-full bg-slate-800/80 border border-slate-700 rounded-xl pl-11 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 transition-all">
                    </div>
                </div>
                <button type="submit"
                    class="w-full bg-gradient-to-r from-rose-600 to-rose-500 hover:from-rose-500 hover:to-rose-400 text-white font-semibold py-3 px-4 rounded-xl shadow-lg shadow-rose-600/30 transition-all flex items-center justify-center gap-2">
                    <i data-lucide="log-in" class="w-4 h-4"></i>
                    대시보드 로그인
                </button>
            </form>
            <p id="loginError" class="text-rose-400 text-xs text-center mt-4 hidden">암호가 올바르지 않습니다.</p>
        </div>
    </div>

    <!-- 2. MAIN DASHBOARD -->
    <div id="dashboardSection" class="hidden min-h-screen flex flex-col">
        <!-- TOP NAV -->
        <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-500">
                        <i data-lucide="bot" class="w-5 h-5"></i>
                    </div>
                    <div>
                        <h2 class="text-sm font-bold text-white flex items-center gap-2">
                            ladypolo AI 비서 <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium">LIVE</span>
                        </h2>
                        <p class="text-xs text-slate-400">Vercel Serverless Multi-Channel Production</p>
                    </div>
                </div>

                <div class="flex items-center gap-4">
                    <button onclick="logout()" class="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 transition-colors">
                        <i data-lucide="log-out" class="w-3.5 h-3.5"></i> 로그아웃
                    </button>
                </div>
            </div>
        </header>

        <!-- DASHBOARD BODY -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-8">
            
            <!-- HEALTH STATUS CARDS -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex items-center gap-4">
                    <div class="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                        <i data-lucide="message-circle" class="w-6 h-6"></i>
                    </div>
                    <div>
                        <div class="text-xs text-slate-400">외부 고객 창구</div>
                        <div class="text-sm font-bold text-white flex items-center gap-1.5 mt-0.5">
                            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> WhatsApp Live
                        </div>
                        <div class="text-[11px] text-slate-500 mt-0.5">+52 1 661 130 9490</div>
                    </div>
                </div>

                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex items-center gap-4">
                    <div class="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                        <i data-lucide="send" class="w-6 h-6"></i>
                    </div>
                    <div>
                        <div class="text-xs text-slate-400">사내 직원 전용 창구</div>
                        <div class="text-sm font-bold text-white flex items-center gap-1.5 mt-0.5">
                            <span class="w-2 h-2 rounded-full bg-sky-500"></span> Telegram (0원)
                        </div>
                        <div class="text-[11px] text-slate-500 mt-0.5">토큰 설정 대기 중</div>
                    </div>
                </div>

                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex items-center gap-4">
                    <div class="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                        <i data-lucide="database" class="w-6 h-6"></i>
                    </div>
                    <div>
                        <div class="text-xs text-slate-400">ERPNext 백엔드</div>
                        <div class="text-sm font-bold text-white flex items-center gap-1.5 mt-0.5">
                            <span class="w-2 h-2 rounded-full bg-blue-500"></span> 실시간 원장 연동
                        </div>
                        <div class="text-[11px] text-slate-500 mt-0.5">ktkpos.frappe.cloud</div>
                    </div>
                </div>

                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex items-center gap-4">
                    <div class="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                        <i data-lucide="sparkles" class="w-6 h-6"></i>
                    </div>
                    <div>
                        <div class="text-xs text-slate-400">Gemini AI 엔진</div>
                        <div class="text-sm font-bold text-white flex items-center gap-1.5 mt-0.5">
                            <span class="w-2 h-2 rounded-full bg-purple-500"></span> 3.5-Flash Cascade
                        </div>
                        <div class="text-[11px] text-slate-500 mt-0.5">응답 지연시간: ~1.5초</div>
                    </div>
                </div>
            </div>

            <!-- SETTINGS FORM & LIVE TEST (2 COLUMNS) -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                <!-- LEFT 2 COLUMNS: SETTINGS -->
                <div class="lg:col-span-2 space-y-6">
                    <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-6">
                        <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                            <div>
                                <h3 class="text-base font-bold text-white flex items-center gap-2">
                                    <i data-lucide="sliders" class="w-5 h-5 text-rose-500"></i> 비즈니스 정책 & 채널 라우팅 설정
                                </h3>
                                <p class="text-xs text-slate-400 mt-0.5">투트랙 메신저 라우팅, 주문 한도, 커스텀 룰북을 실시간 제어합니다.</p>
                            </div>
                            <button onclick="saveAllSettings()" class="bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold px-4 py-2 rounded-xl shadow-lg shadow-rose-600/30 flex items-center gap-1.5 transition-all">
                                <i data-lucide="save" class="w-3.5 h-3.5"></i> 설정 저장
                            </button>
                        </div>

                        <!-- 📡 1. CHANNEL MATRIX ROUTING -->
                        <div class="p-4 bg-slate-800/40 border border-slate-700/60 rounded-2xl space-y-4">
                            <h4 class="text-xs font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
                                <i data-lucide="radio" class="w-4 h-4"></i> 📡 응대 채널 매트릭스 (투트랙 분기)
                            </h4>
                            
                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                                <div class="bg-slate-900/80 p-3.5 rounded-xl border border-slate-700/80 space-y-2">
                                    <div class="font-semibold text-white flex items-center justify-between">
                                        <span>외부 고객 응대 채널</span>
                                        <span class="text-[10px] text-slate-400">손님/바이어</span>
                                    </div>
                                    <div class="flex items-center gap-4 pt-1">
                                        <label class="flex items-center gap-1.5 cursor-pointer">
                                            <input type="radio" name="customerChannel" value="whatsapp" id="custWhatsapp" class="accent-rose-500">
                                            <span class="text-slate-300">WhatsApp (기본)</span>
                                        </label>
                                        <label class="flex items-center gap-1.5 cursor-pointer">
                                            <input type="radio" name="customerChannel" value="telegram" id="custTelegram" class="accent-rose-500">
                                            <span class="text-slate-300">Telegram</span>
                                        </label>
                                    </div>
                                </div>

                                <div class="bg-slate-900/80 p-3.5 rounded-xl border border-slate-700/80 space-y-2">
                                    <div class="font-semibold text-white flex items-center justify-between">
                                        <span>사내 직원 전용 채널</span>
                                        <span class="text-[10px] text-emerald-400">100% 무료</span>
                                    </div>
                                    <div class="flex items-center gap-4 pt-1">
                                        <label class="flex items-center gap-1.5 cursor-pointer">
                                            <input type="radio" name="staffChannel" value="telegram" id="staffTelegram" class="accent-rose-500">
                                            <span class="text-slate-300">Telegram (권장)</span>
                                        </label>
                                        <label class="flex items-center gap-1.5 cursor-pointer">
                                            <input type="radio" name="staffChannel" value="whatsapp" id="staffWhatsapp" class="accent-rose-500">
                                            <span class="text-slate-300">WhatsApp</span>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <!-- 텔레그램 봇 토큰 입력 필드 -->
                            <div class="pt-2">
                                <label class="text-[11px] font-semibold text-slate-300 block mb-1">텔레그램 봇 API 토큰 (BotFather 발급키)</label>
                                <div class="flex gap-2">
                                    <input type="text" id="telegramBotToken" placeholder="예: 7891234567:AAHxxxxxxxx_xxxxxxxxxxxx"
                                        class="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500">
                                    <button type="button" onclick="registerTelegramWebhook()" class="bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-3 py-2 rounded-xl transition-all">
                                        웹훅 등록
                                    </button>
                                </div>
                                <p class="text-[10px] text-slate-500 mt-1">텔레그램 번호 승인 후 토큰을 입력하고 저장을 누르면 즉시 사내 봇이 가동됩니다.</p>
                            </div>
                        </div>

                        <!-- 2. MAX ORDER LIMIT -->
                        <div class="space-y-2">
                            <div class="flex justify-between items-center">
                                <label class="text-xs font-semibold text-slate-300">1회 자동 주문 한도 (임계 금액)</label>
                                <span class="text-xs font-bold text-rose-400" id="limitDisplay">50,000 MXN</span>
                            </div>
                            <p class="text-[11px] text-slate-500">이 금액을 초과하는 대량 주문은 경쟁사 염탐 방지 및 VIP 영업을 위해 담당 지점장 1:1 상담방으로 자동 안내합니다.</p>
                            <div class="relative flex items-center">
                                <input type="number" id="maxOrderLimit" step="5000" min="10000" max="1000000"
                                    class="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-rose-500">
                                <span class="absolute right-4 text-xs text-slate-400 font-semibold">MXN (페소)</span>
                            </div>
                        </div>

                        <!-- 3. TOGGLES -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                            <div class="bg-slate-800/50 border border-slate-700/60 rounded-2xl p-4 flex items-center justify-between">
                                <div>
                                    <div class="text-xs font-semibold text-white">비업무 잡담 엄격 거절</div>
                                    <div class="text-[11px] text-slate-400 mt-0.5">재고/물류 외 질문 차단 (토큰 낭비 방지)</div>
                                </div>
                                <input type="checkbox" id="strictGuardrail" class="w-5 h-5 accent-rose-500 rounded cursor-pointer">
                            </div>

                            <div class="bg-slate-800/50 border border-slate-700/60 rounded-2xl p-4 flex items-center justify-between">
                                <div>
                                    <div class="text-xs font-semibold text-white">3대 퀵 버튼 항상 표시</div>
                                    <div class="text-[11px] text-slate-400 mt-0.5">인사 시 터치식 버튼 발송 (0-Token)</div>
                                </div>
                                <input type="checkbox" id="showQuickButtons" class="w-5 h-5 accent-rose-500 rounded cursor-pointer">
                            </div>
                        </div>

                        <!-- 📜 4. DYNAMIC CUSTOM RULEBOOK -->
                        <div class="pt-4 border-t border-slate-800 space-y-3">
                            <div class="flex items-center justify-between">
                                <div>
                                    <h4 class="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                                        <i data-lucide="book-open" class="w-4 h-4 text-purple-400"></i> 실시간 학습된 매장 커스텀 룰북
                                    </h4>
                                    <p class="text-[11px] text-slate-500 mt-0.5">오너가 메신저로 말한 규칙들이 Supabase DB에 영구 보관되며 실시간 작동합니다.</p>
                                </div>
                                <button onclick="addNewRulePrompt()" class="text-xs text-purple-400 hover:text-purple-300 font-semibold flex items-center gap-1 border border-purple-500/20 bg-purple-500/10 px-3 py-1.5 rounded-lg">
                                    <i data-lucide="plus" class="w-3.5 h-3.5"></i> 규칙 추가
                                </button>
                            </div>

                            <div id="rulebookContainer" class="space-y-2 text-xs">
                            </div>
                        </div>

                        <!-- 🔍 4-1. RULEBOOK AUDIT LOGS (누가 언제 바꿨는지 추적) -->
                        <div class="pt-4 border-t border-slate-800 space-y-3">
                            <div class="flex items-center justify-between">
                                <div>
                                    <h4 class="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                                        <i data-lucide="history" class="w-4 h-4"></i> 룰북 변경 이력 & 감사 로그 (Audit Trail)
                                    </h4>
                                    <p class="text-[11px] text-slate-500 mt-0.5">메신저 및 웹에서 변경된 모든 룰의 변경자, 시간, 채널이 실시간 기록됩니다.</p>
                                </div>
                                <button onclick="loadAuditLogs()" class="text-xs text-slate-400 hover:text-white p-1">
                                    <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
                                </button>
                            </div>

                            <div id="auditLogContainer" class="max-h-48 overflow-y-auto space-y-2 text-xs pr-1">
                                <div class="text-slate-500 text-[11px]">이력을 불러오는 중...</div>
                            </div>
                        </div>

                        <!-- 5. STAFF / BRANCH MANAGEMENT -->
                        <div class="pt-4 border-t border-slate-800 space-y-4">
                            <div class="flex items-center justify-between">
                                <div>
                                    <h4 class="text-xs font-bold text-slate-200 uppercase tracking-wider">지점별 전담 담당자 & 직원 목록 (RBAC)</h4>
                                    <p class="text-[11px] text-slate-500 mt-0.5">등록된 번호는 직원 권한이 부여되며, 대량 주문 시 해당 지점 담당자 방으로 토스됩니다.</p>
                                </div>
                                <button onclick="openAddStaffModal()" class="text-xs text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-1 border border-rose-500/20 bg-rose-500/10 px-3 py-1.5 rounded-lg">
                                    <i data-lucide="plus" class="w-3.5 h-3.5"></i> 직원 추가
                                </button>
                            </div>

                            <div class="overflow-x-auto border border-slate-800 rounded-xl">
                                <table class="w-full text-left text-xs">
                                    <thead class="bg-slate-800/60 text-slate-400 uppercase tracking-wider">
                                        <tr>
                                            <th class="py-3 px-4">이름</th>
                                            <th class="py-3 px-4">전화번호</th>
                                            <th class="py-3 px-4">담당 지점</th>
                                            <th class="py-3 px-4">직책</th>
                                            <th class="py-3 px-4 text-right">관리</th>
                                        </tr>
                                    </thead>
                                    <tbody id="staffTableBody" class="divide-y divide-slate-800 text-slate-300">
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <!-- 6. OWNER PHONES -->
                        <div class="pt-4 border-t border-slate-800 space-y-2">
                            <label class="text-xs font-bold text-slate-200 uppercase tracking-wider">👑 오너/최고관리자 전화번호 목록</label>
                            <p class="text-[11px] text-slate-500">전 창고 상세 재고 및 단가/원가 등 전체 권한이 부여되는 번호입니다 (쉼표로 구분).</p>
                            <input type="text" id="ownerPhones" class="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-rose-500">
                        </div>

                    </div>
                </div>

                <!-- RIGHT 1 COLUMN: LIVE AI TEST SANDBOX -->
                <div class="lg:col-span-1 space-y-6">
                    <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl flex flex-col h-[780px]">
                        <div class="border-b border-slate-800 pb-3 flex items-center justify-between">
                            <div>
                                <h3 class="text-sm font-bold text-white flex items-center gap-1.5">
                                    <i data-lucide="terminal" class="w-4 h-4 text-rose-500"></i> 실시간 대화 샌드박스
                                </h3>
                                <p class="text-[11px] text-slate-400">웹에서 바로 삼돌이에게 질문/이동/룰 학습 테스트</p>
                            </div>
                            <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">Test Bot</span>
                        </div>

                        <!-- CHAT LOG -->
                        <div id="chatLog" class="flex-1 overflow-y-auto py-4 space-y-3 text-xs pr-1">
                            <div class="flex gap-2.5">
                                <div class="w-7 h-7 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
                                    <i data-lucide="bot" class="w-4 h-4"></i>
                                </div>
                                <div class="bg-slate-800 text-slate-200 p-3 rounded-2xl rounded-tl-none max-w-[85%]">
                                    안녕하세요! **ladypolo 비서**입니다.<br>
                                    • `P160 검정 재고` 조회 후<br>
                                    • `이것들 1박스씩 이동 전표 넣어줘`<br>
                                    를 테스트해 보세요!
                                </div>
                            </div>
                        </div>

                        <!-- CHAT INPUT -->
                        <form id="sandboxForm" class="pt-3 border-t border-slate-800 flex gap-2">
                            <input type="text" id="sandboxInput" placeholder="질문을 입력하세요..."
                                class="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500">
                            <button type="submit" class="bg-rose-600 hover:bg-rose-500 text-white px-3.5 py-2 rounded-xl text-xs font-semibold shrink-0 flex items-center justify-center">
                                <i data-lucide="send" class="w-3.5 h-3.5"></i>
                            </button>
                        </form>
                    </div>
                </div>

            </div>

        </main>
    </div>

    <!-- TOAST NOTIFICATION -->
    <div id="toast" class="fixed bottom-6 right-6 bg-emerald-600 text-white text-xs font-semibold px-4 py-3 rounded-xl shadow-2xl transition-all duration-300 transform translate-y-20 opacity-0 flex items-center gap-2 z-50">
        <i data-lucide="check-circle" class="w-4 h-4"></i>
        <span id="toastMsg">설정이 저장되었습니다!</span>
    </div>

    <!-- SCRIPT -->
    <script>
        let currentSettings = {};

        document.addEventListener('DOMContentLoaded', () => {
            lucide.createIcons();
            const token = sessionStorage.getItem('admin_token');
            if (token === 'authenticated') {
                showDashboard();
            }
        });

        // 1. LOGIN
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const pwd = document.getElementById('adminPassword').value;
            try {
                const res = await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'login', password: pwd })
                });
                const data = await res.json();
                if (data.success) {
                    sessionStorage.setItem('admin_token', 'authenticated');
                    showDashboard();
                } else {
                    document.getElementById('loginError').classList.remove('hidden');
                }
            } catch (err) {
                document.getElementById('loginError').innerText = "연결 오류가 발생했습니다.";
                document.getElementById('loginError').classList.remove('hidden');
            }
        });

        function logout() {
            sessionStorage.removeItem('admin_token');
            document.getElementById('dashboardSection').classList.add('hidden');
            document.getElementById('loginSection').classList.remove('hidden');
        }

        async function showDashboard() {
            document.getElementById('loginSection').classList.add('hidden');
            document.getElementById('dashboardSection').classList.remove('hidden');
            lucide.createIcons();
            loadSettings();
            loadAuditLogs();
        }

        async function loadAuditLogs() {
            const container = document.getElementById('auditLogContainer');
            try {
                const res = await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'get_audit_logs' })
                });
                const data = await res.json();
                const logs = data.logs || [];

                if (logs.length === 0) {
                    container.innerHTML = '<div class="text-slate-500 text-[11px] p-2 bg-slate-800/30 rounded-lg">기록된 변경 이력이 없습니다.</div>';
                    return;
                }

                container.innerHTML = '';
                logs.forEach(log => {
                    const timeStr = new Date(log.created_at).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                    const badgeColor = log.channel === 'whatsapp' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : (log.channel === 'telegram' ? 'bg-sky-500/10 text-sky-400 border-sky-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20');
                    
                    const div = document.createElement('div');
                    div.className = 'bg-slate-800/50 border border-slate-700/50 p-2.5 rounded-xl space-y-1';
                    div.innerHTML = `
                        <div class="flex items-center justify-between text-[10px]">
                            <span class="font-bold text-slate-300 flex items-center gap-1.5">
                                <span class="px-1.5 py-0.5 rounded border uppercase text-[9px] ${badgeColor}">${log.channel || 'web'}</span>
                                ${log.changed_by_name || '관리자'} (${log.changed_by_phone || 'admin'})
                            </span>
                            <span class="text-slate-500 font-mono">${timeStr}</span>
                        </div>
                        <div class="text-slate-200 text-xs pl-1">
                            ${log.rule_content}
                        </div>
                    `;
                    container.appendChild(div);
                });
                lucide.createIcons();
            } catch (err) {
                container.innerHTML = '<div class="text-rose-400 text-[11px]">이력 로드 실패: ' + err + '</div>';
            }
        }

        async function loadSettings() {
            try {
                const res = await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'get_settings' })
                });
                currentSettings = await res.json();

                document.getElementById('maxOrderLimit').value = currentSettings.max_auto_order_limit || 50000;
                document.getElementById('limitDisplay').innerText = (currentSettings.max_auto_order_limit || 50000).toLocaleString() + ' MXN';
                document.getElementById('strictGuardrail').checked = currentSettings.strict_business_guardrail !== false;
                document.getElementById('showQuickButtons').checked = currentSettings.show_quick_buttons !== false;
                document.getElementById('ownerPhones').value = (currentSettings.owner_phones || []).join(', ');
                document.getElementById('telegramBotToken').value = currentSettings.telegram_bot_token || '';

                if (currentSettings.customer_channel === 'telegram') {
                    document.getElementById('custTelegram').checked = true;
                } else {
                    document.getElementById('custWhatsapp').checked = true;
                }

                if (currentSettings.staff_channel === 'whatsapp') {
                    document.getElementById('staffWhatsapp').checked = true;
                } else {
                    document.getElementById('staffTelegram').checked = true;
                }

                renderRules(currentSettings.tenant_custom_rules || []);
                renderStaffTable(currentSettings.staff_members || []);
            } catch (err) {
                console.error("설정 로드 실패:", err);
            }
        }

        function renderRules(rules) {
            const container = document.getElementById('rulebookContainer');
            container.innerHTML = '';
            rules.forEach((r, idx) => {
                const div = document.createElement('div');
                div.className = 'flex items-start justify-between bg-slate-800/60 border border-slate-700/60 p-3 rounded-xl';
                div.innerHTML = `
                    <div class="text-slate-300 pr-2 leading-relaxed">• ${r}</div>
                    <button onclick="removeRule(${idx})" class="text-rose-400 hover:text-rose-300 shrink-0 p-1">
                        <i data-lucide="x" class="w-3.5 h-3.5"></i>
                    </button>
                `;
                container.appendChild(div);
            });
            lucide.createIcons();
        }

        function addNewRulePrompt() {
            const rule = prompt("추가할 매장 운영 규칙을 입력하세요 (예: 50,000페소 이상 주문은 Monse 담당자에게 토스):");
            if (!rule) return;
            if (!currentSettings.tenant_custom_rules) currentSettings.tenant_custom_rules = [];
            currentSettings.tenant_custom_rules.push(rule);
            renderRules(currentSettings.tenant_custom_rules);
            showToast("새 규칙이 추가되었습니다 (설정 저장을 눌러주세요)");
        }

        function removeRule(idx) {
            currentSettings.tenant_custom_rules.splice(idx, 1);
            renderRules(currentSettings.tenant_custom_rules);
            showToast("규칙이 삭제되었습니다 (설정 저장을 눌러주세요)");
        }

        function renderStaffTable(staffList) {
            const tbody = document.getElementById('staffTableBody');
            tbody.innerHTML = '';
            staffList.forEach((st, idx) => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-800/40 transition-colors';
                tr.innerHTML = `
                    <td class="py-3 px-4 font-semibold text-white">${st.name}</td>
                    <td class="py-3 px-4 text-slate-400 font-mono">${st.phone}</td>
                    <td class="py-3 px-4"><span class="px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-[10px]">${st.branch}</span></td>
                    <td class="py-3 px-4 text-slate-400">${st.role || '직원'}</td>
                    <td class="py-3 px-4 text-right">
                        <button onclick="removeStaff(${idx})" class="text-rose-400 hover:text-rose-300 p-1">
                            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            lucide.createIcons();
        }

        function openAddStaffModal() {
            const name = prompt("직원 이름 (예: Monse):");
            if (!name) return;
            const phone = prompt("전화번호 (국가번호 포함, 예: 5215512345678):");
            if (!phone) return;
            const branch = prompt("담당 지점명 (예: IKEA, TIENDA, ALARCON):", "IKEA");
            if (!branch) return;
            const role = prompt("직책 (예: 지점 매니저):", "지점 매니저");

            if (!currentSettings.staff_members) currentSettings.staff_members = [];
            currentSettings.staff_members.push({ name, phone, branch, role });
            renderStaffTable(currentSettings.staff_members);
            showToast("직원이 추가되었습니다 (설정 저장을 눌러주세요)");
        }

        function removeStaff(idx) {
            if (confirm("정말 이 직원을 삭제하시겠습니까?")) {
                currentSettings.staff_members.splice(idx, 1);
                renderStaffTable(currentSettings.staff_members);
                showToast("직원이 삭제되었습니다 (설정 저장을 눌러주세요)");
            }
        }

        async function registerTelegramWebhook() {
            const token = document.getElementById('telegramBotToken').value.trim();
            if (!token) {
                alert("텔레그램 봇 토큰을 먼저 입력해 주세요.");
                return;
            }
            try {
                const res = await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'register_telegram_webhook', token: token })
                });
                const data = await res.json();
                if (data.success) {
                    showToast("✅ 텔레그램 웹훅 등록 성공!");
                } else {
                    alert("웹훅 등록 결과: " + JSON.stringify(data));
                }
            } catch (e) {
                alert("등록 오류: " + e);
            }
        }

        async function saveAllSettings() {
            const newLimit = parseInt(document.getElementById('maxOrderLimit').value) || 50000;
            const strictG = document.getElementById('strictGuardrail').checked;
            const showQB = document.getElementById('showQuickButtons').checked;
            const tgToken = document.getElementById('telegramBotToken').value.trim();
            const ownerRaw = document.getElementById('ownerPhones').value;
            const owners = ownerRaw.split(',').map(s => s.trim()).filter(s => s.length > 0);

            const custChannel = document.querySelector('input[name="customerChannel"]:checked')?.value || 'whatsapp';
            const staffChannel = document.querySelector('input[name="staffChannel"]:checked')?.value || 'telegram';

            const payload = {
                action: 'save_settings',
                settings: {
                    max_auto_order_limit: newLimit,
                    strict_business_guardrail: strictG,
                    show_quick_buttons: showQB,
                    customer_channel: custChannel,
                    staff_channel: staffChannel,
                    telegram_bot_token: tgToken,
                    owner_phones: owners,
                    staff_members: currentSettings.staff_members || [],
                    tenant_custom_rules: currentSettings.tenant_custom_rules || []
                }
            };

            const res = await fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                showToast("✅ 설정이 성공적으로 저장되었습니다!");
                loadSettings();
            } else {
                alert("저장 실패");
            }
        }

        function showToast(msg) {
            const toast = document.getElementById('toast');
            document.getElementById('toastMsg').innerText = msg;
            toast.classList.remove('translate-y-20', 'opacity-0');
            setTimeout(() => {
                toast.classList.add('translate-y-20', 'opacity-0');
            }, 3000);
        }

        // SANDBOX CHAT SIMULATOR
        document.getElementById('sandboxForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('sandboxInput');
            const q = input.value.trim();
            if (!q) return;

            const chatLog = document.getElementById('chatLog');
            
            const uDiv = document.createElement('div');
            uDiv.className = 'flex justify-end gap-2.5';
            uDiv.innerHTML = `<div class="bg-rose-600 text-white p-3 rounded-2xl rounded-tr-none max-w-[85%]">${q}</div>`;
            chatLog.appendChild(uDiv);
            input.value = '';
            chatLog.scrollTop = chatLog.scrollHeight;

            const tDiv = document.createElement('div');
            tDiv.id = 'typingIndicator';
            tDiv.className = 'flex gap-2.5';
            tDiv.innerHTML = `
                <div class="w-7 h-7 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
                    <i data-lucide="bot" class="w-4 h-4"></i>
                </div>
                <div class="bg-slate-800 text-slate-400 p-3 rounded-2xl rounded-tl-none max-w-[85%] animate-pulse">
                    답변 작성 중...
                </div>
            `;
            chatLog.appendChild(tDiv);
            lucide.createIcons();
            chatLog.scrollTop = chatLog.scrollHeight;

            try {
                const res = await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'test_agent', message: q })
                });
                const data = await res.json();
                document.getElementById('typingIndicator')?.remove();

                const botDiv = document.createElement('div');
                botDiv.className = 'flex gap-2.5';
                botDiv.innerHTML = `
                    <div class="w-7 h-7 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
                        <i data-lucide="bot" class="w-4 h-4"></i>
                    </div>
                    <div class="bg-slate-800 text-slate-100 p-3 rounded-2xl rounded-tl-none max-w-[85%] whitespace-pre-wrap leading-relaxed">${data.reply}</div>
                `;
                chatLog.appendChild(botDiv);
                lucide.createIcons();
                chatLog.scrollTop = chatLog.scrollHeight;
            } catch (err) {
                document.getElementById('typingIndicator')?.remove();
            }
        });
    </script>
</body>
</html>
"""
