# Report 06 — Frontend Pages (Jinja2 Templates)

> Reference cho Phase 04 + 05 + 07. List + spec từng template.

## Template inheritance

```
base.html (Tailwind CDN + HTMX CDN + navbar + footer)
  ├── landing.html
  ├── register.html
  ├── login.html
  ├── goal_select.html
  ├── topic_list.html
  ├── theory.html
  ├── quiz.html
  │     └── _quiz_card.html (HTMX swap partial)
  ├── quiz_result.html
  ├── dashboard.html
  ├── history.html
  ├── recommend.html
  └── admin_clusters.html
```

## base.html

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>{% block title %}Tin học 10{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-slate-50 text-slate-900">
  <nav class="...">...</nav>
  <main class="container mx-auto p-4">
    {% block content %}{% endblock %}
  </main>
  <footer class="...">...</footer>
  {% block scripts %}{% endblock %}
</body>
</html>
```

## Page-by-page spec

### 1. landing.html
- **Route:** GET /
- **Auth:** optional
- **Mô tả:** Hero + 3-feature highlight + CTA "Đăng ký / Đăng nhập"
- **HTMX:** none
- **Components:** hero card, feature grid 3 col

### 2. register.html
- **Route:** GET /register, POST /register
- **Auth:** none
- **Mô tả:** Form username + password + password2
- **HTMX:** `hx-post="/register"` `hx-swap="outerHTML"` cho live validation (optional)
- **Components:** form card centered

### 3. login.html
- **Route:** GET /login, POST /login
- **Auth:** none
- **Mô tả:** Form đăng nhập + link tới /register
- **HTMX:** none (full form POST)

### 4. goal_select.html
- **Route:** GET /goal, POST /goal
- **Auth:** session
- **Mô tả:** 4 radio card cho goal_type (Ôn thi / Học chủ đề mới / Cải thiện điểm yếu / Thử thách)
- **HTMX:** none
- **Components:** card grid 2x2 với icon + label + radio hidden

### 5. topic_list.html
- **Route:** GET /topics
- **Auth:** session
- **Mô tả:** List 4 topic kèm progress bar (mastery%), nút "Bắt đầu quiz" + "Xem lý thuyết"
- **HTMX:** none
- **Components:** topic card 4 cái, progress bar Tailwind

### 6. theory.html
- **Route:** GET /theory/{topic_id}
- **Auth:** session
- **Mô tả:** Markdown render từ `data/theory/topic-XX.md`, sidebar nav 4 topic, nút "Làm quiz" cuối page
- **HTMX:** `hx-get` sidebar link để switch topic
- **Components:** sidebar nav + main content (prose class Tailwind typography plugin hoặc manual)

### 7. quiz.html
- **Route:** GET /quiz/{topic_id}
- **Auth:** session
- **Mô tả:** Container cho quiz card, progress "Câu X/N", quiz state hidden inputs
- **HTMX:** include `_quiz_card.html` partial ban đầu
- **JS:** `quiz_timer.js` set `window.questionStart = Date.now()`
- **Components:** progress bar, quiz card container `<div id="quiz-card">`

### 8. _quiz_card.html (PARTIAL)
- **Route:** trả về từ POST /quiz/answer
- **Mô tả:** Question content + 4 option radio + button submit + hidden response_time
- **HTMX:** form `hx-post="/quiz/answer" hx-target="#quiz-card" hx-swap="outerHTML"`
- **Critical:** include `<script>updateTimer()</script>` để re-arm timer mỗi swap
- **End state:** trả về HTML có `<div hx-redirect="/quiz/result/{session_id}">` hoặc trigger `HX-Redirect` header

### 9. quiz_result.html
- **Route:** GET /quiz/result/{session_id}
- **Auth:** session
- **Mô tả:** Score X/N, % accuracy, list câu sai (collapsible) + đáp án đúng + giải thích, 2 button "Dashboard" / "Quiz lại"
- **HTMX:** collapsible reveal câu sai dùng `hx-on` hoặc Alpine.js (optional)

### 10. dashboard.html
- **Route:** GET /dashboard
- **Auth:** session
- **Mô tả:** Greeting + radar chart 4 topic mastery + ability θ + cluster card + top 3 recommend
- **HTMX:** none (page load đủ)
- **Components:**
  - Header: "Xin chào {{ user.username }}"
  - Stat card: ability θ, total attempts, accuracy
  - **Radar chart canvas** (Chart.js)
  - Cluster card: "Bạn thuộc nhóm: Trung bình"
  - Recommendation list 3 card
- **Chart.js setup:**
  ```js
  new Chart(ctx, {
    type: 'radar',
    data: {
      labels: {{ topic_names|tojson }},
      datasets: [{
        label: 'Mastery (%)',
        data: {{ mastery_values|tojson }},
        backgroundColor: 'rgba(59,130,246,0.2)',
        borderColor: 'rgb(59,130,246)'
      }]
    },
    options: { scales: { r: { min: 0, max: 100 } } }
  });
  ```

### 11. history.html
- **Route:** GET /history?topic=X&page=Y
- **Auth:** session
- **Mô tả:** Table Attempt: thời gian, câu hỏi, đúng/sai, response time. Filter dropdown topic + paging.
- **HTMX:** `hx-get` cho filter dropdown change → swap table tbody

### 12. recommend.html
- **Route:** GET /recommend
- **Auth:** session
- **Mô tả:** 3 card recommendation với explain text + button "Bắt đầu"
- **HTMX:** none
- **Components:** card grid 1x3

### 13. admin_clusters.html
- **Route:** GET /admin/clusters
- **Auth:** admin
- **Mô tả:** Scatter plot Chart.js (PCA 2D) + bảng thống kê 3 cluster + nút refresh
- **HTMX:** `hx-post="/admin/clusters/refresh"` cho refresh button
- **Chart.js scatter setup:**
  ```js
  new Chart(ctx, {
    type: 'scatter',
    data: {
      datasets: [
        { label: 'Yếu', data: [...{x,y}], backgroundColor: 'red' },
        { label: 'TB', data: [...], backgroundColor: 'yellow' },
        { label: 'Giỏi', data: [...], backgroundColor: 'green' }
      ]
    }
  });
  ```

## Component patterns

### Quiz progress bar (Tailwind)
```html
<div class="w-full bg-slate-200 rounded-full h-2">
  <div class="bg-blue-600 h-2 rounded-full" style="width: {{ percent }}%"></div>
</div>
```

### Option radio card
```html
<label class="block p-4 border rounded-lg cursor-pointer hover:bg-slate-100">
  <input type="radio" name="answer" value="{{ opt.key }}" class="mr-2">
  {{ opt.text }}
</label>
```

### Recommendation card
```html
<div class="bg-white p-4 rounded-lg shadow">
  <h3 class="font-bold">{{ rec.topic_name }}</h3>
  <p class="text-sm text-slate-600">{{ rec.explanation }}</p>
  <a href="/quiz/{{ rec.topic_id }}" class="...">Bắt đầu →</a>
</div>
```

## HTMX patterns used

| Pattern | Where |
|---|---|
| `hx-post + hx-swap=outerHTML` | quiz submit |
| `hx-get + hx-target` | filter dropdown history |
| `HX-Redirect` header | end-of-quiz |
| `hx-disabled-elt="this"` | prevent double-submit |
| `hx-on::after-swap` | re-arm timer JS |

## quiz_timer.js

```javascript
window.questionStart = Date.now();
function updateTimer() {
  window.questionStart = Date.now();
}
document.body.addEventListener('htmx:beforeRequest', function(e) {
  const form = e.detail.elt;
  const inp = form.querySelector('input[name=response_time_ms]');
  if (inp) inp.value = Date.now() - window.questionStart;
});
document.body.addEventListener('htmx:afterSwap', updateTimer);
```

## Unresolved questions

- Dùng Tailwind Typography plugin (`prose`) cho theory render không (cần CDN riêng)?
- Có dùng Alpine.js cho collapsible/dropdown hay HTMX đủ?
- Mobile responsive ở mức nào (chỉ verify cơ bản hay design hẳn)?
- Dark mode support?
- Toast notification cho lỗi/success (HTMX trigger event)?
