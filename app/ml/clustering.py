"""K-means student segmentation (BRAINSTORM §5.3).

Cluster học sinh thành K=3 nhóm (Yếu / Trung bình / Giỏi) dựa trên 4 đặc trưng:

    1. avg_mastery          — mastery trung bình các topic (BKT output).
    2. avg_response_time_ms — thời gian trả lời trung bình.
    3. total_attempts       — tổng số câu đã làm (mức độ hoạt động).
    4. accuracy_hard        — độ chính xác trên câu khó (difficulty_level == 3).

Pipeline: StandardScaler → KMeans(k=3) → đặt tên cluster theo avg_mastery của
tâm cụm. PCA 2D để vẽ scatter plot cho báo cáo.

K cố định = 3 (khớp 3 nhóm trong spec) — không dùng elbow method cho demo.
Citation: MacQueen, J. (1967). "Some methods for classification and analysis of
multivariate observations." Berkeley Symposium on Math. Stat. and Probability.
"""
from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sqlmodel import Session, select

from app.ml.recommender import DEFAULT_MASTERY
from app.models import Attempt, MasteryState, Question, User

FEATURE_NAMES = ["avg_mastery", "avg_response_time_ms", "total_attempts", "accuracy_hard"]
DEFAULT_K = 3
RANDOM_STATE = 42

# Tên cluster theo thứ tự avg_mastery tăng dần (chỉ dùng khi k == 3).
CLUSTER_NAMES_K3 = ["Yếu", "Trung bình", "Giỏi"]


def build_features(session: Session) -> tuple[list[int], list[str], np.ndarray]:
    """Trả (user_ids, usernames, feature_matrix) cho mọi user.

    feature_matrix shape = (n_users, 4) theo thứ tự FEATURE_NAMES.
    User không có attempt vẫn được tính (feature = mặc định/0).
    """
    users = session.exec(select(User).order_by(User.id)).all()
    # Nạp toàn bộ câu hỏi 1 lần (tránh N+1 query trong vòng lặp attempt).
    difficulty_by_qid = {
        q.id: q.difficulty_level for q in session.exec(select(Question)).all()
    }
    user_ids: list[int] = []
    usernames: list[str] = []
    rows: list[list[float]] = []

    for u in users:
        masteries = session.exec(
            select(MasteryState.p_mastery).where(MasteryState.user_id == u.id)
        ).all()
        avg_mastery = float(np.mean(masteries)) if masteries else DEFAULT_MASTERY

        attempts = session.exec(
            select(Attempt).where(Attempt.user_id == u.id)
        ).all()
        total_attempts = len(attempts)
        avg_rt = (
            float(np.mean([a.response_time_ms for a in attempts])) if attempts else 0.0
        )

        # Accuracy trên câu khó (difficulty_level == 3).
        hard_total = 0
        hard_correct = 0
        for a in attempts:
            if difficulty_by_qid.get(a.question_id) == 3:
                hard_total += 1
                hard_correct += 1 if a.is_correct else 0
        accuracy_hard = (hard_correct / hard_total) if hard_total else 0.0

        user_ids.append(u.id)
        usernames.append(u.username)
        rows.append([avg_mastery, avg_rt, float(total_attempts), accuracy_hard])

    return user_ids, usernames, np.array(rows, dtype=float)


def cluster_users(
    features: np.ndarray, k: int = DEFAULT_K
) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    """Chuẩn hóa rồi KMeans. Trả (labels, scaled_features, scaler).

    Yêu cầu n_samples >= k.
    """
    if features.shape[0] < k:
        raise ValueError(f"Cần ít nhất {k} user để phân {k} cụm (hiện có {features.shape[0]}).")

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    # Cột zero-variance (mọi user giống nhau) → StandardScaler trả 0; phòng NaN.
    scaled = np.nan_to_num(scaled, nan=0.0, posinf=0.0, neginf=0.0)
    km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE)
    labels = km.fit_predict(scaled)
    return labels, scaled, scaler


def name_clusters(features: np.ndarray, labels: np.ndarray, k: int = DEFAULT_K) -> dict[int, str]:
    """Map mỗi cluster label → tên, xếp theo avg_mastery (cột 0) tăng dần.

    Với k == 3 dùng ['Yếu', 'Trung bình', 'Giỏi']; khác thì 'Nhóm i'.
    """
    avg_mastery_by_label: dict[int, float] = {}
    for lbl in range(k):
        members = features[labels == lbl]
        avg_mastery_by_label[lbl] = float(members[:, 0].mean()) if len(members) else 0.0

    ordered = sorted(avg_mastery_by_label, key=lambda l: avg_mastery_by_label[l])
    names = CLUSTER_NAMES_K3 if k == 3 else [f"Nhóm {i + 1}" for i in range(k)]
    return {lbl: names[rank] for rank, lbl in enumerate(ordered)}


def reduce_pca_2d(scaled_features: np.ndarray) -> np.ndarray:
    """Chiếu features (đã scale) xuống 2D bằng PCA cho scatter plot."""
    n_components = min(2, scaled_features.shape[0], scaled_features.shape[1])
    pca = PCA(n_components=n_components, random_state=RANDOM_STATE)
    coords = np.nan_to_num(pca.fit_transform(scaled_features), nan=0.0)
    # Đảm bảo luôn 2 cột (pad 0 nếu chỉ 1 component).
    if coords.shape[1] < 2:
        coords = np.hstack([coords, np.zeros((coords.shape[0], 2 - coords.shape[1]))])
    return coords


def analyze_clusters(session: Session, k: int = DEFAULT_K) -> dict:
    """Pipeline đầy đủ cho endpoint admin. Trả dict sẵn sàng render/scatter.

    Khi không đủ user (< k) → {'ok': False, 'reason': ...}.
    """
    user_ids, usernames, features = build_features(session)
    if len(user_ids) < k:
        return {
            "ok": False,
            "reason": f"Cần ít nhất {k} người dùng để phân cụm (hiện có {len(user_ids)}).",
            "n_users": len(user_ids),
            "k": k,
        }

    labels, scaled, _ = cluster_users(features, k)
    label_names = name_clusters(features, labels, k)
    coords = reduce_pca_2d(scaled)

    points = []
    for i, uid in enumerate(user_ids):
        points.append({
            "user_id": uid,
            "username": usernames[i],
            "cluster": int(labels[i]),
            "cluster_name": label_names[int(labels[i])],
            "x": round(float(coords[i, 0]), 3),
            "y": round(float(coords[i, 1]), 3),
            "avg_mastery": round(float(features[i, 0]), 3),
            "avg_response_time_ms": round(float(features[i, 1]), 1),
            "total_attempts": int(features[i, 2]),
            "accuracy_hard": round(float(features[i, 3]), 3),
        })

    summary = []
    for lbl in range(k):
        members = [p for p in points if p["cluster"] == lbl]
        if not members:
            continue
        summary.append({
            "cluster": lbl,
            "name": label_names[lbl],
            "size": len(members),
            "avg_mastery": round(sum(m["avg_mastery"] for m in members) / len(members), 3),
            "usernames": [m["username"] for m in members],
        })
    summary.sort(key=lambda s: s["avg_mastery"])

    return {
        "ok": True,
        "k": k,
        "n_users": len(user_ids),
        "feature_names": FEATURE_NAMES,
        "points": points,
        "summary": summary,
    }


def user_cluster_name(session: Session, user_id: int, k: int = DEFAULT_K) -> str | None:
    """Tên cluster của một user (None nếu không đủ dữ liệu / user không tồn tại)."""
    result = analyze_clusters(session, k)
    if not result["ok"]:
        return None
    for p in result["points"]:
        if p["user_id"] == user_id:
            return p["cluster_name"]
    return None
