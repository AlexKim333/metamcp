# 👗 ladypolo WhatsApp AI 비서 & WMS ERPNext 연동 프로젝트 요약 보고서
**작성일시:** 2026-08-21  
**배포 플랫폼:** Vercel Serverless Production ([https://metamcp-one.vercel.app](https://metamcp-one.vercel.app))  
**버전:** v1.0.0-PROD  

---

## 🌟 1. 프로젝트 개요
Meta WhatsApp Cloud API와 ERPNext(`ktkpos.frappe.cloud`), Google Gemini 최신 AI 엔진을 결합하여, 멕시코 현장 직원·관리자·고객이 스마트폰 WhatsApp을 통해 24시간 실시간 재고 조회, 전표 조회, 주문서 자동 작성을 0.1~1.5초 만에 수행하는 **지능형 물류/영업 자동화 시스템**입니다.

---

## 🚀 2. 구현 완료된 8대 핵심 기능

### ① 0-Token 초고속 로컬 바이패스 엔진 (`text_preprocessor.py`)
- 인사(`hola`, `안녕`), 창고 목록(`almacenes`), 단순 재고 질의(`P-160 rojo 재고`) 등 정형 질의를 AI(Gemini) 호출 없이 파이썬 로컬에서 **0.01~0.3초(0토큰)** 만에 즉각 회신.
- 비용 0원 & Vercel 10초 타임아웃 완벽 방어.

### ② 스페인어 / 한국어 세션 언어 지속성 (Language Persistence)
- 스페인어로 첫 인사(`hola`)를 나눈 접속자는 이후 언어가 없는 순수 코드(`P-160-ROJO-400`, `3331`)만 입력하더라도 **끝까지 100% 스페인어로 일관되게 응답**.
- 한국어로 질문 시 즉시 한국어 모드로 자연스럽게 자동 전환.

### ③ 재고 조회 3대 핵심 철칙 탑재
- **[철칙 1]** 질문한 특정 품목/컬러 1개만 집중 답변 (묻지 않은 다른 색상 줄줄이 나열 금지).
- **[철칙 2]** 박스(Cajas/Bultos) 수량과 낱개(Piezas) 총수량 필수 명시.
- **[철칙 3]** 3~4줄 이내 초간결 단답형 (모바일 최적화 & 토큰 낭비 방지).

### ④ 접속자별 역할 권한 시스템 (RBAC: `roles.py`)
- **오너/최고관리자 (Owner):** 대표님 번호 자동 인식 $\rightarrow$ 전 창고 상세 재고, 원가/단가, 전표 생성 전체 열람 (Full Access).
- **지점 직원 (Staff):** Monse, Nadya 등 등록 직원 $\rightarrow$ 본사/지점 가용 재고 확인, 지점 이동 전표 확인 및 주문 생성.
- **일반 고객 (Customer):** 미등록 외부 번호 $\rightarrow$ 내부 창고명 비공개, 가용 재고 유무(있음/품절) 및 소비자 단가 위주 안전 안내.

### ⑤ WhatsApp 3대 인터랙티브 퀵 버튼 (`whatsapp_client.py`)
- 채팅창에 `안녕`, `hola`, `메뉴` 입력 시 터치 가능한 3개 버튼 팝업:
  - 🔘 `[ 📦 재고 조회 ]` ➔ 품목 입력 가이드 (0토큰)
  - 🔘 `[ 📋 최근 이동 전표 ]` ➔ ERPNext 최근 5건 전표 현황 즉답 (0토큰)
  - 🔘 `[ ❓ 사용 안내 ]` ➔ 사용법 요약 즉답 (0토큰)

### ⑥ VIP 대량 주문 방어 & 1:1 담당자 딥링크 (Click-to-Chat)
- 1회 주문 한도(기본 50,000 MXN) 초과 시 경쟁사 염탐 방지 및 VIP 영업을 위해 자동 차단.
- 담당 지점장(Monse 등)과의 **1:1 개인 톡방 이동 버튼(wa.me 딥링크)**을 띄우고, **장바구니 요약 텍스트가 담당자 대화창에 자동으로 채워져(Pre-filled)** 고객이 전송만 누르면 비용 0원으로 1:1 상담 개시.

### ⑦ 포워딩 주문 ➔ ERPNext Sales Order 자동 등록 & 정식 영수증 발행
- 지점장이 고객과 1:1 상담 후 확정된 카톡/와츠앱 메시지를 삼돌이에게 [전달(Forward)]하면:
  - AI가 품목, 박스 수량, 단가, 지점, 고객명을 자동 파싱.
  - **ERPNext 백엔드에 `Sales Order (판매 주문서)` 즉시 정식 등록** (`SO-2026-xxxxx`).
  - 박스 $\times$ 입수량 = 총 수량 계산 후 [전표 번호, 소계, 총액]이 정리된 깔끔한 정식 영수증 회신.

### ⑧ 통합 관리자 웹 대시보드 포털 (`dashboard_ui.py`)
- **접속 주소:** [https://metamcp-one.vercel.app](https://metamcp-one.vercel.app) (비밀번호: `ladypolo2026!`)
- 브라우저에서 1회 주문 한도(MXN), 지점별 직원/담당자 추가/삭제, AI 가드레일 토글 스위치 실시간 제어.
- 우측 실시간 AI 샌드박스 채팅창으로 웹에서 즉시 테스트 가능.

---

## 🔑 3. 시스템 자격증명 및 접속 정보

| 항목 | 정보 |
| :--- | :--- |
| **관리자 포털** | `https://metamcp-one.vercel.app` (암호: `ladypolo2026!`) |
| **Meta Webhook URL** | `https://metamcp-one.vercel.app/webhook` |
| **Verify Token** | `ktk_wms_webhook_secret_2026` |
| **WhatsApp 발신 번호** | `+52 1 661 130 9490` (`ladypolo`, 삼돌이 프로필 적용 완료) |
| **ERPNext 인스턴스** | `https://ktkpos.frappe.cloud` (Company: `kecon`) |
| **Google Gemini 모델** | `gemini-3.5-flash` (Primary, 응답 속도 ~1.5초) |
| **GitHub 저장소** | `https://github.com/AlexKim333/metamcp.git` (main 브랜치) |

---

## 🛣️ 4. 향후 확장 과제 (Next Steps)
1. 현장 직원 실전 대화 패턴 피드백 수집 및 동의어/품목코드 매핑 고도화.
2. 검증된 삼돌이 두뇌(전처리 정규화, 퍼지 검색 엔진)를 웹/모바일 앱(`ktk-wms-v2/SamdoriBrain.js`)으로 역이식.
3. 지점 간 재고 이동(Material Transfer) 드래프트 생성 도구 추가.
