# 03: 経験値獲得フィードバック機能 詳細設計

## 概要

学習ログを記録した際に、獲得した経験値やレベルアップをユーザーに視覚的にフィードバックする機能。
「経験値を獲得！」ボタンを押した後、何が起きたのかが一目でわかるようにする。

---

## 現状の課題

- フォーム送信後、同じページにリダイレクトされるだけで **何も表示が変わらない**
- 経験値をいくつ獲得したのか、現在のレベルがいくつなのかが **フィードバックされない**
- レベルアップしても気づけない

---

## 実装方針

### 表示する情報（3段階）

| 段階 | 条件 | 表示内容 |
|------|------|----------|
| **① 通常フィードバック** | 毎回 | 「🎯 +150 XP 獲得！（動画5本 × 10xp + 問題20問 × 5xp）」 |
| **② レベルアップ通知** | レベルが上がった時 | 「⚔️ LEVEL UP! Lv.3 → Lv.4」 |
| **③ 科目クリア通知** | 動画進捗100%到達時 | 「🏆 消化管を制覇した！『消化管の覇者』の称号を獲得！」 |

### XP計算ロジック

```python
# 1回の記録で獲得するXP
gained_xp = (study_video_count × 10) + (solve_count × 5) + (study_time × 2)
```

### レベル計算ロジック

```python
# 現行: 累計学習時間ベース
# total_minutes = 全StudyLogのstudy_timeの合計
# level = int(total_minutes / 60) + 1

# 提案: 累計XPベースに変更
# total_xp = 全StudyLogから算出した累計XP
# level = int(total_xp / 500) + 1
# → 500XPごとにレベルアップ（調整可能）
```

---

## 変更対象ファイル

### 1. `logs/views.py` — XP計算 & セッションへの保存

**変更内容**: POST成功時に獲得XP・レベル変動・科目クリアを計算し、Djangoの `messages` フレームワークで通知する。

```python
# 変更後のイメージ
from django.contrib import messages

@login_required
def record_quest(request):
    if request.method == "POST":
        form = StudyLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.save()

            # --- ここから追加 ---

            # ① 獲得XP計算
            gained_xp = (log.study_video_count * 10) + (log.solve_count * 5) + (log.study_time * 2)
            messages.success(request, f"🎯 +{gained_xp} XP 獲得！")

            # ② レベルアップ判定
            my_logs = StudyLog.objects.filter(user=request.user)
            # 記録前のXP（今回のログを除く）
            from django.db.models import Sum, F
            all_logs = my_logs.aggregate(
                total_videos=Sum('study_video_count'),
                total_solves=Sum('solve_count'),
                total_time=Sum('study_time'),
            )
            total_xp = (
                (all_logs['total_videos'] or 0) * 10
                + (all_logs['total_solves'] or 0) * 5
                + (all_logs['total_time'] or 0) * 2
            )
            old_xp = total_xp - gained_xp
            new_level = int(total_xp / 500) + 1
            old_level = int(old_xp / 500) + 1

            if new_level > old_level:
                messages.warning(request, f"⚔️ LEVEL UP! Lv.{old_level} → Lv.{new_level}")

            # ③ 科目クリア判定
            subject = log.subject
            current_videos = my_logs.filter(subject=subject).aggregate(
                total=Sum('study_video_count')
            )['total'] or 0
            if subject.total_video_count > 0 and current_videos >= subject.total_video_count:
                # クリア前のチェック（今回の記録でちょうど到達したか）
                prev_videos = current_videos - log.study_video_count
                if prev_videos < subject.total_video_count:
                    messages.info(request, f"🏆 {subject.name}を制覇した！『{subject.name}の覇者』の称号を獲得！")

            # --- ここまで追加 ---

            return redirect("record_quest")
    # ... 以下既存のGET処理
```

### 2. `config/settings.py` — messagesフレームワーク確認

`django.contrib.messages` は Django にデフォルトで含まれている。
`INSTALLED_APPS` と `MIDDLEWARE` に以下があることを確認するだけ（通常は設定済み）:

```python
INSTALLED_APPS = [
    ...
    'django.contrib.messages',  # 確認
]

MIDDLEWARE = [
    ...
    'django.contrib.messages.middleware.MessageMiddleware',  # 確認
]
```

### 3. `logs/templates/logs/record.html` — 通知の表示UI

**変更内容**: フォームの上にメッセージ表示エリアを追加。

```html
<!-- フォームの上に追加 -->
{% if messages %}
<div class="notification-area">
    {% for message in messages %}
    <div class="notification {{ message.tags }}">
        {{ message }}
    </div>
    {% endfor %}
</div>
{% endif %}
```

**追加CSS**:

```css
/* 通知エリア */
.notification-area {
    margin-bottom: 20px;
}
.notification {
    padding: 15px 20px;
    border-radius: 8px;
    margin-bottom: 10px;
    font-size: 18px;
    font-weight: bold;
    animation: slideIn 0.5s ease-out, fadeOut 0.5s ease-in 4.5s forwards;
}

/* ① 通常XP獲得 (success = 緑) */
.notification.success {
    background: linear-gradient(135deg, #1a472a, #2d6a4f);
    border: 2px solid #52b788;
    color: #b7e4c7;
}

/* ② レベルアップ (warning = 金) */
.notification.warning {
    background: linear-gradient(135deg, #5a4000, #7a5a00);
    border: 2px solid #ffd700;
    color: #ffd700;
    font-size: 22px;
    text-align: center;
}

/* ③ 科目クリア (info = 紫) */
.notification.info {
    background: linear-gradient(135deg, #2d1b69, #4a2c8a);
    border: 2px solid #b388ff;
    color: #e0c0ff;
    font-size: 20px;
    text-align: center;
}

/* アニメーション */
@keyframes slideIn {
    from { transform: translateY(-20px); opacity: 0; }
    to   { transform: translateY(0); opacity: 1; }
}
@keyframes fadeOut {
    from { opacity: 1; }
    to   { opacity: 0; }
}
```

### 4. `logs/views.py` (GET側) — レベル計算の統一

現行の `total_level` 計算もXPベースに統一する:

```python
# 現行
total_minutes = my_logs.aggregate(Sum("study_time"))["study_time__sum"] or 0
total_level = int(total_minutes / 60) + 1

# 変更後
all_agg = my_logs.aggregate(
    total_videos=Sum('study_video_count'),
    total_solves=Sum('solve_count'),
    total_time=Sum('study_time'),
)
total_xp = (
    (all_agg['total_videos'] or 0) * 10
    + (all_agg['total_solves'] or 0) * 5
    + (all_agg['total_time'] or 0) * 2
)
total_level = int(total_xp / 500) + 1
```

contextに `total_xp` も追加してテンプレートで表示:

```python
context = {
    "form": form,
    "subject_status_list": subject_status_list,
    "total_level": total_level,
    "total_xp": total_xp,             # 追加
    "next_level_xp": total_level * 500, # 次のレベルまでのXP
}
```

---

## 画面イメージ

```
┌──────────────────────────────────────────────┐
│  🎯 +150 XP 獲得！                           │  ← 毎回表示（緑）
├──────────────────────────────────────────────┤
│  ⚔️ LEVEL UP! Lv.3 → Lv.4                   │  ← レベルアップ時（金）
├──────────────────────────────────────────────┤
│  🏆 消化管を制覇した！                        │  ← 科目クリア時（紫）
│  『消化管の覇者』の称号を獲得！                │
└──────────────────────────────────────────────┘

🔥 MediQuest - 勇者 admin の冒険 🔥
   Lv.4 | 1,850 XP | 次のレベルまで 150 XP

📝 クエストを記録する
┌─────────────────────────┐
│ 科目:  [消化管 ▼]       │
│ 教材:  [Q-Assist ▼]     │
│ 動画:  [5] 本            │
│ 問題:  [20] 問           │
│ 時間:  [30] 分           │
│                          │
│  [経験値を獲得！]         │
└─────────────────────────┘
```

---

## 実装手順

1. `config/settings.py` で `messages` フレームワークが有効か確認
2. `logs/views.py` のPOST処理にXP計算・レベルアップ判定・科目クリア判定を追加
3. `logs/views.py` のGET処理のレベル計算をXPベースに統一
4. `logs/templates/logs/record.html` に通知表示エリアとCSSを追加
5. テンプレートにレベル・XP表示を追加
