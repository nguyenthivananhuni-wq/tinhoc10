# Report 04 — ML Algorithms Spec

> Reference cho Phase 05, 06, 07. 3 thuật toán.

---

## 1. Bayesian Knowledge Tracing (BKT)

### Citation
Corbett, A. T., & Anderson, J. R. (1995). "Knowledge tracing: Modeling the acquisition of procedural knowledge." *User Modeling and User-Adapted Interaction*, 4(4), 253-278.

### Params (default từ paper)

| Param | Symbol | Default | Ý nghĩa |
|---|---|---|---|
| Initial knowledge | P(L₀) | 0.1 | Xác suất biết trước khi học |
| Transition (learn) | P(T) | 0.2 | XS chuyển từ chưa-biết → biết sau 1 exposure |
| Guess | P(G) | 0.2 | XS đoán đúng khi chưa biết |
| Slip | P(S) | 0.1 | XS sai khi đã biết |

### Formula

**Bước 1 — Posterior given observation:**

Nếu correct:
```
P(L_t | correct) = P(L_t) * (1 - P(S)) / [P(L_t) * (1 - P(S)) + (1 - P(L_t)) * P(G)]
```

Nếu incorrect:
```
P(L_t | incorrect) = P(L_t) * P(S) / [P(L_t) * P(S) + (1 - P(L_t)) * (1 - P(G))]
```

**Bước 2 — Apply transition:**
```
P(L_{t+1}) = P(L_t | obs) + (1 - P(L_t | obs)) * P(T)
```

### Pseudo-code

```python
@dataclass
class BktParams:
    p_l0: float = 0.1
    p_t: float = 0.2
    p_g: float = 0.2
    p_s: float = 0.1

def update_mastery(prev_p: float, is_correct: bool, params: BktParams) -> float:
    if is_correct:
        numerator = prev_p * (1 - params.p_s)
        denominator = numerator + (1 - prev_p) * params.p_g
    else:
        numerator = prev_p * params.p_s
        denominator = numerator + (1 - prev_p) * (1 - params.p_g)
    
    posterior = numerator / denominator if denominator > 0 else prev_p
    new_p = posterior + (1 - posterior) * params.p_t
    return max(0.0, min(1.0, new_p))
```

### Integration với Attempt

```
POST /quiz/answer:
  1. Insert Attempt row
  2. question.topic_id → fetch MasteryState(user_id, topic_id)
  3. prev_p = mastery.p_mastery (default 0.1 nếu không có)
  4. new_p = update_mastery(prev_p, is_correct, default_params)
  5. mastery.p_mastery = new_p, mastery.last_updated = now()
  6. commit
```

### Test cases

| Case | Input | Expected |
|---|---|---|
| 1 | prev=0.1, correct=True | p > 0.1 |
| 2 | prev=0.1, correct=False | p < 0.2 |
| 3 | start=0.1, 5×correct | p > 0.85 |
| 4 | CICIC alternating | p oscillate mid 0.3-0.6 |
| 5 | prev=0.99, correct=True | p ≤ 1.0 |

---

## 2. Item Response Theory (IRT) 1-PL Rasch

### Citation
Rasch, G. (1960). *Probabilistic Models for Some Intelligence and Attainment Tests.* Foundation của TOEFL/GMAT adaptive testing.

### Formula

```
P(correct | θ, b) = 1 / (1 + exp(-(θ - b)))
```

- θ = ability của user (User.ability_theta)
- b = difficulty câu hỏi (Question.difficulty_b)
- Khoảng giá trị thực tế: θ, b ∈ [-3, 3]

### Ability Estimation — MLE đơn giản (gradient ascent)

```python
def log_likelihood(theta: float, responses: list[tuple[float, bool]]) -> float:
    ll = 0.0
    for b, correct in responses:
        p = 1.0 / (1.0 + np.exp(-(theta - b)))
        p = max(1e-6, min(1 - 1e-6, p))  # avoid log(0)
        ll += np.log(p) if correct else np.log(1 - p)
    return ll

def estimate_ability(responses: list[tuple[float, bool]], 
                     max_iter: int = 50, lr: float = 0.1) -> float:
    if not responses:
        return 0.0
    theta = 0.0
    for _ in range(max_iter):
        # gradient = sum(observed - expected)
        grad = sum(
            (1 if c else 0) - (1.0 / (1.0 + np.exp(-(theta - b))))
            for b, c in responses
        )
        theta += lr * grad
        theta = max(-4.0, min(4.0, theta))   # clamp
    return theta
```

**Alternative:** EAP (Expected A Posteriori) — more stable nhưng phức tạp hơn. MVP dùng MLE.

### Difficulty Calibration (batch)

Cho mỗi câu hỏi q có ≥10 response:
```
p_correct = correct_count / total_count
b ≈ -log(p_correct / (1 - p_correct))   # logit
```

Skip nếu <10 response → giữ b=0.

### Adaptive Question Selection

```python
def select_question(user, topic_id, session, exclude_ids=None) -> Question:
    candidates = session.exec(
        select(Question)
        .where(Question.topic_id == topic_id)
        .where(Question.id.notin_(exclude_ids or []))
    ).all()
    if not candidates:
        return None
    # min |b - θ|, target Fisher info max at θ=b
    candidates.sort(key=lambda q: abs(q.difficulty_b - user.ability_theta))
    return candidates[0]
```

### Test cases

| Case | Input | Expected |
|---|---|---|
| 1 | prob_correct(0, 0) | == 0.5 |
| 2 | 10/10 on b=0 | θ > 0 |
| 3 | 0/10 on b=0 | θ < 0 |
| 4 | 5/10 mix on b=0 | θ ≈ 0, tol 0.3 |
| 5 | 3 correct b=-1, 0 correct b=2 | -1 < θ < 1 |

---

## 3. K-means Clustering

### Citation
MacQueen (1967). Standard sklearn implementation.

### Features (4 dimensions per user)

| Feature | Compute |
|---|---|
| avg_mastery | mean(MasteryState.p_mastery) cho user |
| avg_response_time_ms | mean(Attempt.response_time_ms) |
| total_attempts | count(Attempt) |
| accuracy_difficulty_3 | sum(is_correct AND difficulty_level=3) / count(difficulty_level=3) |

### Preprocessing

```python
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)         # normalize z-score

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
labels = kmeans.fit_predict(X_scaled)
centers = kmeans.cluster_centers_
```

### Cluster Naming (deterministic by avg_mastery center)

```python
# Sắp cluster theo avg_mastery của center
mastery_idx = 0  # column 0 của feature matrix
order = np.argsort(centers[:, mastery_idx])
name_map = {order[0]: "Yếu", order[1]: "Trung bình", order[2]: "Giỏi"}
```

### Visualization (PCA 2D cho scatter plot)

```python
pca = PCA(n_components=2)
X_2d = pca.fit_transform(X_scaled)
# Pass X_2d + labels + name_map → Chart.js scatter
```

### Test scenario (demo data)

Tạo 3 user pattern:
- **alice_weak:** mastery low (0.2), slow time, many wrong on diff=3.
- **bob_avg:** mastery 0.5, moderate time, 50% on diff=3.
- **carol_strong:** mastery 0.8, fast time, 90% on diff=3.

→ KMeans tách rõ 3 cluster trong scatter.

---

## Integration Diagram

```
[User submits answer]
        │
        ▼
[Insert Attempt] ──► [BKT update MasteryState]
                            │
                            ▼
[End of session] ──► [IRT estimate θ] ──► [Update User.ability_theta]
                            │
                            ▼
[Recommendation Engine]
  - goal_type (LearningGoal)
  - mastery_vector (MasteryState)
  - ability_theta (User)
        │
        ▼
[Pick topic by goal rule]
        │
        ▼
[Pick question by |b - θ| min]
        │
        ▼
[Render next quiz card]

[Admin trigger] ──► [K-means cluster all users]
                            │
                            ▼
                    [Scatter plot dashboard]
```

## Unresolved questions

- BKT: tự code (~80 dòng, defendable) hay dùng `pyBKT`?
- IRT: stick với MLE hay EAP cho stability?
- θ user: 1 global vs per-topic (4 vector)?
- K-means: k=3 fixed hay elbow auto-pick?
- Recalibrate cron daily hay manual admin trigger?
