# 👑 MetaMCP: B2B 플러그인에서 토탈 ERP 플랫폼으로의 상용화 마스터 로드맵
> **(Master Commercialization Blueprint & System Context Handover Document)**  
> *본 문서는 새로운 AI 모델이나 세션이 시작될 때 시스템의 기술 아키텍처, 사업 전략, 특허 현황, 향후 상용화 로드맵을 1초 만에 완벽하게 이해하고 연속성 있게 기획/개발할 수 있도록 정리된 최상위 마스터 문서입니다.*

---

## 📌 1. 프로젝트 정체성 및 핵심 비전 (Executive Summary)

* **프로젝트명:** MetaMCP (ladypolo AI WMS)
* **서비스 링크:** [https://metamcp-one.vercel.app](https://metamcp-one.vercel.app)
* **저장소(GitHub):** `https://github.com/AlexKim333/metamcp.git`
* **사업 비전:**
  1. **[1단계 출발점 - 경량 B2B 플러그인 SaaS]:** 기존 전산망(ERPNext, Shopify, 커스텀 DB)을 그대로 쓰면서 메신저(WhatsApp/Telegram)로 실시간 물류·재고·주문을 5분 만에 제어하는 무코드 플러그인 서비스.
  2. **[2단계 - 다중 채널 이식 및 제로코드 현지화]:** 메타 요금 정책을 회피하는 투트랙(WhatsApp+Telegram) 채널 라우팅과, 오너의 발화만으로 매장 규칙이 실시간 각인되는 적응형 AI 비서.
  3. **[3단계 최종 목표 - 프라뻬(Frappe) 통합 토탈 솔루션]:** 단순 챗봇을 넘어 자체 프라뻬 WMS/ERP 백엔드 + 다중 메신저 AI 에이전트가 완벽 결합된 글로벌 올인원 엔터프라이즈 물류 플랫폼으로 확장.

---

## ⚙️ 2. 현재 100% 가동 중인 핵심 기술 인프라 (Tech Stack)

```
       [ 외부 고객 (B2B/B2C) ]                 [ 사내 직원 / 지점 매니저 ]
       (WhatsApp Cloud API)                   (0원 무료 Telegram Bot API)
                 │                                        │
                 └──────────────────┬─────────────────────┘
                                    ▼
       ┌─────────────────────────────────────────────────────────────┐
       │     👑 Vercel Serverless 중앙 AI 두뇌 (Python / FastAPI)     │
       │  • 0-Token 로컬 전처리 바이패스 (Meta API 비용 90% 절감)     │
       │  • 120초 유령 메시지 방어 (사용자 이탈 시 정중한 대기 전환)     │
       │  • Gemini 3.5 / 3.6 Flash 자율 도구 라우팅 (MCP 엔진)        │
       └──────────────┬───────────────────────────────┬──────────────┘
                      │                               │
                      ▼                               ▼
       ┌──────────────────────────────┐ ┌──────────────────────────────┐
       │   🗄️ Supabase PostgreSQL     │ │    🏭 Frappe / ERPNext Cloud │
       │  • staff_members (직원 RBAC) │ │  • Item (3,000+ SKU 품목)   │
       │  • owner_phones (오너 마스터) │ │  • Bin (10개 창고 실시간 재고)│
       │  • tenant_settings (매장설정)│ │  • Stock Entry (이동 전표)   │
       │  • tenant_rules (실시간 룰북)│ │  • Material Request (청구서) │
       │  • rulebook_audit_logs (감사)│ │  • Sales Order (판매 주문서) │
       └──────────────────────────────┘ └──────────────────────────────┘
```

### 💎 가동 중인 8대 독점 기능
1. **20개 전 색상 재고 그리드 매트릭스 (`get_item_grid_matrix`):**  
   `P160 그리드` 또는 *"어떤 색상 남아있어?"* 발화 시, 20개 전 색상의 본사/지점별 박스·낱개 수량을 일목요연한 표(Grid Table)로 0.1초 만에 즉시 출력.
2. **세션 메모리 추적 기반 1박스 일괄 재고이동 Draft (`create_material_transfer_draft`):**  
   직원이 연속 조회한 품목들을 FIFO 큐에 캐싱 ➔ *"이것들 1박스씩 이동 전표 넣어줘"* 발화 시 `Stock Entry` Draft 즉시 발행.
3. **지점 정식 재고 청구 제출 (`create_material_request_submit`):**  
   지점에서 본사(알라르꼰)로 재고 보충 요청 시 `Material Request` (Submitted / docstatus=1) 자동 발행.
4. **포워딩 텍스트 기반 판매 주문서 등록 (`create_sales_order`):**  
   관리자가 고객과 나눈 견적/주문 텍스트를 톡으로 포워딩하면 신규 고객 생성 및 `Sales Order` 즉시 등록.
5. **대화형 제로코드 룰북 학습 (`save_tenant_rule`):**  
   오너가 메신저로 *"1회 주문 5만 페소 초과 시 지점장 토스"* 발화 시, Supabase DB 영구 저장 및 AI 프롬프트 실시간 주입.
6. **룰북 변경 이력 감사 로그 (Audit Trail):**  
   누가, 언제, 어떤 메신저 채널(WhatsApp/Telegram/Web)에서 룰을 바꿨는지 Supabase `rulebook_audit_logs`에 초단위 영구 기록.
7. **의도 기반 룰 상충 방지 프로토콜 (Intent-based Rule Hierarchy):**  
   단순 키워드 던짐(`P160`) ➔ 특정화 역질문 / 명시적 복수 질문(`무슨 색 있어?`) ➔ 그리드 매트릭스 전체 출력으로 충돌 원천 방지.
8. **0-Token 로컬 바이패스 & 120초 유령 메시지 방어:**  
   수사/색상 정규화 및 고객 응답 지연 시 wa.me 딥링크 제공 후 세션 자동 종료.

---

## 🎯 3. Meta 정책 대응 투트랙(Two-Track) 다중 채널 전략

* **배경:** Meta의 WhatsApp Cloud API 정책 변경으로 인한 메시지당 과금 및 24시간 세션 요금 리스크 발생.
* **해결책 (투트랙 채널 매트릭스):**
  * **사내 채널 (직원, 지점장, 창고 관리자):** **100% 무료인 Telegram Bot API**로 전면 라우팅 (API 비용 0원, 재고 조회 무제한).
  * **대외 채널 (외부 도소매 고객):** **WhatsApp Cloud API**로 응대하되, 1턴당 다량의 정보(전 색상 그리드 + 박스당 가격)를 한 번에 패키징하여 전송 ➔ 톡 횟수를 극적으로 줄여 과금 최소화.
  * **대량 주문 오프로딩:** 50,000 MXN 이상 대량 거래 시 `wa.me/전화번호` 1:1 담당 지점장 다이렉트 딥링크로 토스하여 Meta API 세션 즉시 종료.

---

## 🗺️ 4. 단계별 비즈니스 상용화 로드맵 (Commercialization Roadmap)

```
  [ Phase 1: 플러그인 B2B SaaS ] ➔ [ Phase 2: 다중채널 & 멀티테넌트 ] ➔ [ Phase 3: 프라뻬 토탈 ERP 플랫폼 ]
  - 타사 ERP/POS 연결 플러그인       - WhatsApp + Telegram + Web        - Frappe 호스팅 + AI 번들
  - 5분 원클릭 온보딩                - 테넌트별 룰북/감사로그 격리      - 중남미/글로벌 올인원 공급
  - 월 구독형 (\$49 ~ \$99/월)        - 메타 요금 절감 엔진 탑재         - 대기업 커스텀 SI 시장 장악
```

### 🚀 Phase 1: 경량 플러그인 B2B SaaS (출발점 - 현 단계)
* **목표:** 기존 ERPNext, Shopify, 자체 POS를 쓰는 도소매 업체들이 **소스코드 변경 없이 5분 만에 AI 물류 비서를 도입**하게 만들기.
* **사용자 온보딩 흐름:**
  1. 웹 대시보드([metamcp](https://metamcp-one.vercel.app))에서 매장 회원가입.
  2. 고객사의 ERP URL & API Key 입력 (ERPNext, Shopify, WooCommerce 등).
  3. 메타 비즈니스 ID 또는 텔레그램 봇 토큰 입력.
  4. **완료:** 그 매장 오너가 메신저로 룰북을 지시하면 즉시 현장 가동.
* **과금 모델:** 매장당 월 \$49 ~ \$99 B2B 구독 모델.

### 🌐 Phase 2: 다중 채널 확장 및 멀티 테넌시 강화
* **목표:** 메타 과금 정책으로부터 100% 안전한 다중 채널(Telegram, WhatsApp, Web Chat Widget, 카카오톡 등) 매트릭스 완성.
* **주요 기능:**
  * 테넌트별 DB 완전 격리 (Supabase Multi-tenancy).
  * 룰북 버전 관리(Rollback 기능) 및 지점별 권한(RBAC) 커스텀 UI 제공.
  * 멕시코/중남미 패션·의류·도소매 협회 및 한인 도매상 연합 대상 1차 타깃 영업.

### 👑 Phase 3: 프라뻬(Frappe) 통합 토탈 솔루션 (최종 목적지)
* **목표:** 단순 AI 플러그인을 넘어, **"ERPNext 기반 클라우드 WMS/POS + 메신저 AI 에이전트"가 결합된 완전체 토탈 엔터프라이즈 플랫폼** 공급.
* **사업 모델:**
  * ERP 전산이 없는 중소 사업체에게 **"프라뻬 WMS 인스턴스 + 모바일 AI 비서 + 관리자 대시보드"를 통째로 턴키(Turn-key) 공급**.
  * 고가의 대기업 SI(수억 원대) 솔루션을 대체하여, 월 \$299 ~ \$500 수준의 압도적 가성비 올인원 ERP 플랫폼으로 글로벌 시장(멕시코, 북미, 동남아) 독점.

---

## 📜 5. 특허 및 지식재산권(IP) 보호 현황

대한민국 특허청(KIPO) 및 PCT 국제특허 출원용 발명 명세서가 완성되어 있습니다 ([`PATENT_SPECIFICATION_DRAFT.md`](file:///c:/Users/tukpa/OneDrive/바탕%20화면/meta%20연동프로젝트/PATENT_SPECIFICATION_DRAFT.md)).

### 12대 핵심 특허 청구항:
1. **0-Token 로컬 전처리 및 수사/색상 정규화 바이패스**
2. **120초 유령 메시지 방어 및 대기 큐 전환 시스템**
3. **wa.me 딥링크를 통한 Meta API 세션 조기 오프로딩 및 비용 절감**
4. **최근 조회 세션 FIFO 큐 기반 1박스 일괄 Stock Entry Draft 발행 메커니즘**
5. **메신저 대화형 룰북 동적 주입 및 영구 감사 로그(Audit Trail) 저장**
6. **포워딩 텍스트 자연어 파싱 기반 ERPNext Sales Order 자동 등록**
7. **지점별 권한(RBAC) 연동 Material Request 정식 제출 분기**
8. **단일 키워드 vs 다중 집계 의도 기반 룰 상충 방지 계층 (Rule Hierarchy)**
9. **모델 캐스케이드(Gemini 3.5 ➔ 3.6 ➔ 3.1) 및 비상 로컬 폴백 장애 복구**
10. **외수/사내 투트랙(WhatsApp vs Telegram) 채널 매트릭스 스위칭**
11. **커스텀 그리드 그룹(`custom_grid_group_id`) 기반 전 색상 매트릭스 집계**
12. **다중 테넌트 이기종 ERP(MCP Adapter) 연결 프로토콜**

---

## 🤖 6. 새로운 AI 모델 / 세션 인계용 프롬프트 (Handover Prompt)

새로운 채팅창이나 다른 AI 모델에게 아래 문구를 복사해서 전달하면 모든 맥락을 완벽히 이어받습니다:

```text
안녕하세요! 저는 'MetaMCP(ladypolo AI WMS)' 프로젝트의 마스터 아키텍트입니다.
저희 프로젝트의 상세 아키텍처, 8대 기능, 투트랙 채널 전략, 12대 특허 청구항,
그리고 [플러그인 B2B SaaS ➔ 다중채널 확장 ➔ 프라뻬 통합 토탈 ERP 플랫폼]으로 이어지는 3단계 상용화 로드맵은
프로젝트 루트의 'MASTER_COMMERCIALIZATION_BLUEPRINT.md'와 'PATENT_SPECIFICATION_DRAFT.md'에 완벽히 정리되어 있습니다.
이 파일들을 기준으로 상용화 전략, 백엔드 고도화, 권한 분리 연동 작업을 계속해서 진행해 주세요!
```
