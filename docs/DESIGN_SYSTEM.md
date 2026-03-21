# HireKit Design System

HireKit 프로젝트의 디자인 원칙과 스타일 가이드.

---

## 1. Design Principles

### 1.1 명확함 (Clarity)
- 한 화면에 하나의 메시지. 복잡한 정보는 단계별로 나눠서 보여준다.
- "이게 뭔지" 3초 안에 알 수 있어야 한다.

### 1.2 일관성 (Consistency)
- 같은 기능은 같은 모양. 버튼, 카드, 텍스트 스타일을 통일한다.
- 메인 페이지, 데모, 문서 모두 같은 디자인 언어를 사용한다.

### 1.3 여백 (Breathing Room)
- 정보를 밀어넣지 않는다. 넉넉한 여백으로 읽기 편하게 한다.
- 섹션 간 최소 80px, 요소 간 최소 16px 간격.

### 1.4 신뢰감 (Trust)
- 수치와 근거를 먼저 보여준다. "감"이 아닌 "데이터" 기반.
- 출처를 명시하고, 불확실한 정보는 솔직하게 표시한다.

---

## 2. Color System

### Primary
```css
--color-primary: #3182F6;       /* HireKit 블루 — 핵심 CTA, 링크, 강조 */
--color-primary-hover: #1B64DA;
--color-primary-light: #EBF3FE; /* 배경 하이라이트 */
```

### Neutral (Light Theme — 기본)
```css
--color-bg: #FFFFFF;            /* 페이지 배경 */
--color-bg-secondary: #F4F5F7; /* 카드, 섹션 배경 */
--color-bg-tertiary: #EAEBEE;  /* 구분선, 비활성 */
--color-text-primary: #191F28; /* 본문 제목 */
--color-text-secondary: #4E5968; /* 본문 */
--color-text-tertiary: #8B95A1; /* 캡션, 보조 */
--color-border: #E5E8EB;       /* 카드 테두리 */
```

### Neutral (Dark Theme)
```css
--color-bg-dark: #17171C;
--color-bg-secondary-dark: #1E1E24;
--color-bg-tertiary-dark: #2C2C35;
--color-text-primary-dark: #F2F4F6;
--color-text-secondary-dark: #B0B8C1;
--color-text-tertiary-dark: #6B7684;
--color-border-dark: #2C2C35;
```

### Semantic
```css
--color-success: #00C471;      /* 긍정, 완료, Grade S/A */
--color-warning: #FF9500;      /* 주의, Grade C */
--color-danger: #FF4545;       /* 위험, 에러, Grade D */
--color-info: #3182F6;         /* 정보, 안내 */
```

### Grade Colors
```css
--grade-s: #3182F6;  /* S등급 — 블루 */
--grade-a: #00C471;  /* A등급 — 그린 */
--grade-b: #FF9500;  /* B등급 — 오렌지 */
--grade-c: #FF6B00;  /* C등급 — 딥오렌지 */
--grade-d: #FF4545;  /* D등급 — 레드 */
```

---

## 3. Typography

### Font Family
```css
--font-sans: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

### Scale (PC 기준)
| Token | Size | Weight | Line Height | 용도 |
|-------|------|--------|-------------|------|
| `display` | 48px | 700 | 1.3 | Hero 제목 |
| `h1` | 36px | 700 | 1.4 | 섹션 제목 |
| `h2` | 28px | 700 | 1.4 | 서브 제목 |
| `h3` | 22px | 600 | 1.5 | 카드 제목 |
| `body-lg` | 18px | 400 | 1.7 | 본문 강조 |
| `body` | 16px | 400 | 1.7 | 기본 본문 |
| `body-sm` | 14px | 400 | 1.6 | 캡션, 보조 |
| `caption` | 12px | 400 | 1.5 | 레이블, 배지 |
| `mono` | 14px | 400 | 1.6 | 코드, 터미널 |

---

## 4. Spacing System

8px 기반 그리드:
```
4px   — 아이콘과 텍스트 간격
8px   — 인라인 요소 간격
12px  — 작은 패딩 (배지, 태그)
16px  — 기본 패딩, 요소 간격
24px  — 카드 내부 패딩
32px  — 섹션 내 블록 간격
48px  — 섹션 간 간격 (모바일)
80px  — 섹션 간 간격 (PC)
120px — Hero 여백
```

---

## 5. Components

### Button
```
Primary:   bg=#3182F6, text=white, rounded=12px, h=48px, px=24px
Secondary: bg=#F4F5F7, text=#191F28, rounded=12px, h=48px, px=24px
Ghost:     bg=transparent, text=#3182F6, border=1px #3182F6, rounded=12px
Small:     h=36px, px=16px, text=14px
```

### Card
```
bg=white (light) / #1E1E24 (dark)
border=1px #E5E8EB (light) / none (dark)
rounded=16px
padding=24px
shadow=none (그림자 대신 배경색 대비로 구분)
hover: translate-y=-2px, shadow=0 4px 12px rgba(0,0,0,0.08)
```

### Badge
```
filled:  bg=#EBF3FE, text=#3182F6, rounded=8px, px=8px, py=4px
success: bg=#E8F7EF, text=#00C471
warning: bg=#FFF3E0, text=#FF9500
danger:  bg=#FFEBEE, text=#FF4545
```

### Input
```
bg=#F4F5F7 (light) / #2C2C35 (dark)
border=none (테두리 없는 filled input)
rounded=12px
h=48px
px=16px
focus: border=2px #3182F6
```

### Navigation (PC)
```
h=64px
bg=white/80 backdrop-blur
position=fixed top
border-bottom=1px #E5E8EB
max-width=1200px centered
```

### Scorecard (HireKit 전용)
```
Score Ring: stroke=#3182F6, bg=#F4F5F7, rounded=full
Dimension Bar: bg=#3182F6, height=8px, rounded=4px
Grade Badge: font=mono, size=caption, filled badge with grade color
```

---

## 6. Layout

### Max Width
```
content: 1080px
narrow: 680px (텍스트 중심 페이지)
wide: 1200px (카드 그리드)
```

### Grid
```
PC: 12-column, gap=24px
Tablet: 8-column, gap=16px
Mobile: 4-column, gap=16px
```

### Section Structure
```html
<section class="py-20">           <!-- 80px 상하 여백 -->
  <div class="max-w-[1080px] mx-auto px-6">
    <h2>섹션 제목</h2>             <!-- h2: 28px bold -->
    <p class="mt-3 text-secondary">설명</p>
    <div class="mt-10 grid grid-cols-3 gap-6">
      <!-- 카드들 -->
    </div>
  </div>
</section>
```

---

## 7. UX Writing

### 톤앤매너
- **해요체** 사용 (한국어 페이지)
- **능동형** 문장 (수동형 최소화)
- **긍정형** 표현 ("~할 수 없어요" 대신 "~하면 할 수 있어요")

### 예시
```
❌ "분석이 완료되었습니다"
✅ "분석이 끝났어요"

❌ "API 키가 설정되지 않았습니다"
✅ "API 키를 설정하면 더 많은 데이터를 볼 수 있어요"

❌ "오류가 발생했습니다"
✅ "지금은 데이터를 가져올 수 없어요. 잠시 후 다시 시도해주세요"

❌ "취소"
✅ "닫기"
```

### CTA 문구
```
"지금 시작하기" (primary)
"데모 체험하기" (secondary)
"GitHub에서 보기" (link)
"pip install hirekit" (code CTA)
```

---

## 8. Motion

### Transition
```css
--transition-fast: 150ms ease;
--transition-normal: 250ms ease;
--transition-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);
```

### Interaction
- hover: `transform: translateY(-2px)` + subtle shadow (카드)
- click: `transform: scale(0.98)` (버튼)
- page entry: `opacity 0→1, translateY 20px→0` (fade up, 400ms)
- score animation: `stroke-dashoffset` 1200ms (스코어 링)

### 원칙
- 화려한 애니메이션 지양. 의미 있는 전환만 사용.
- scroll-triggered animation은 한 번만 실행 (반복 금지).

---

## 9. 다크 모드

- 기본: 시스템 설정 따름 (`prefers-color-scheme`)
- 수동 토글: 헤더 우측
- 원칙: 단순히 색 반전이 아니라, 각 표면(surface) 레이어의 명도를 조정

```
Light: bg=#FFF → card=#F4F5F7 → input=#EAEBEE
Dark:  bg=#17171C → card=#1E1E24 → input=#2C2C35
```

---

## 10. 페이지별 적용

### 메인 (index.html)
- 배경: 흰색 (light), 다크 (dark)
- Hero: 큰 제목 + 한 줄 설명 + CTA 2개 (설치/데모)
- Feature 카드: 3열 그리드, 아이콘 + 제목 + 설명
- 데이터 소스: 리스트 카드, 배지로 상태 표시
- Footer: 간결하게

### 데모 (demo.html)
- 위자드 스텝: 상단 프로그레스 바 (1→2→3→4)
- 각 스텝: 중앙 정렬, 최대 680px (narrow)
- 결과: 탭 UI, 스코어카드 시각화, 카드 기반 리포트

### 공통
- 같은 nav, 같은 footer, 같은 색상, 같은 폰트
- Pretendard 폰트 (한국어 최적화 오픈소스 폰트)
