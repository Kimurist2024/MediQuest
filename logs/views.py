from django.shortcuts import render, redirect
from django.db.models import Sum
from django.contrib.auth.decorators import login_required  # ← 追加
from .forms import StudyLogForm
from .models import StudyLog, Subject


# ↓ これをつけると「ログインしてない人は入れない（ログイン画面に飛ばされる）」ようになる
@login_required
def record_quest(request):
    if request.method == "POST":
        form = StudyLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)

            # 【重要変更】ユーザーID=1 ではなく「現在のユーザー」をセット
            log.user = request.user

            log.save()
            return redirect("record_quest")
    else:
        form = StudyLogForm()

    subjects = Subject.objects.all()
    subject_status_list = []

    # 【重要変更】全データではなく「自分のデータ」だけで計算する！
    # filter(user=request.user) を追加しています
    my_logs = StudyLog.objects.filter(user=request.user)

    total_minutes = my_logs.aggregate(Sum("study_time"))["study_time__sum"] or 0
    total_level = int(total_minutes / 60) + 1

    for subject in subjects:
        # ここも「自分のログ」だけで科目ごとに絞り込む
        logs = my_logs.filter(subject=subject)

        current_videos = (
            logs.aggregate(Sum("study_video_count"))["study_video_count__sum"] or 0
        )

        video_progress = 0
        if subject.total_video_count > 0:
            video_progress = int((current_videos / subject.total_video_count) * 100)

        subject_status_list.append(
            {
                "name": subject.name,
                "current_val": current_videos,
                "total_val": subject.total_video_count,
                "video_progress": min(video_progress, 100),
                "image_url": subject.image.url if subject.image else None,
            }
        )

    context = {
        "form": form,
        "subject_status_list": subject_status_list,
        "total_level": total_level,
    }
    return render(request, "logs/record.html", context)
