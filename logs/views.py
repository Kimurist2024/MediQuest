import json
from collections import defaultdict

from django.shortcuts import render, redirect
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import StudyLogForm
from .models import StudyLog, Subject


def calc_xp(videos, solves, minutes):
    """XPを計算する: 動画×10 + 問題×5 + 時間×2"""
    return (videos or 0) * 10 + (solves or 0) * 5 + (minutes or 0) * 2


def calc_total_xp(logs_queryset):
    """QuerySetから累計XPを算出"""
    agg = logs_queryset.aggregate(
        total_videos=Sum('study_video_count'),
        total_solves=Sum('solve_count'),
        total_time=Sum('study_time'),
    )
    return calc_xp(agg['total_videos'], agg['total_solves'], agg['total_time'])


@login_required
def record_quest(request):
    if request.method == "POST":
        form = StudyLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user

            # 記録前のXPとレベルを取得
            my_logs = StudyLog.objects.filter(user=request.user)
            old_xp = calc_total_xp(my_logs)
            old_level = int(old_xp / 500) + 1

            # 科目クリア前の動画数を取得
            prev_videos = my_logs.filter(subject=log.subject).aggregate(
                total=Sum('study_video_count')
            )['total'] or 0

            log.save()

            # ① 獲得XP通知
            gained_xp = calc_xp(log.study_video_count, log.solve_count, log.study_time)
            messages.success(request, f"🎯 +{gained_xp} XP 獲得！")

            # ② レベルアップ判定
            new_xp = old_xp + gained_xp
            new_level = int(new_xp / 500) + 1
            if new_level > old_level:
                messages.warning(request, f"⚔️ LEVEL UP! Lv.{old_level} → Lv.{new_level}")

            # ③ 科目クリア判定
            subject = log.subject
            new_videos = prev_videos + log.study_video_count
            if subject.total_video_count > 0 and new_videos >= subject.total_video_count and prev_videos < subject.total_video_count:
                messages.info(request, f"🏆 {subject.name}を制覇した！『{subject.name}の覇者』の称号を獲得！")

            return redirect("record_quest")
    else:
        form = StudyLogForm()

    subjects = Subject.objects.all()
    subject_status_list = []

    my_logs = StudyLog.objects.filter(user=request.user)

    # XPベースのレベル計算
    total_xp = calc_total_xp(my_logs)
    total_level = int(total_xp / 500) + 1
    next_level_xp = total_level * 500

    for subject in subjects:
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
        "total_xp": total_xp,
        "next_level_xp": next_level_xp,
    }
    return render(request, "logs/record.html", context)


@login_required
def stats(request):
    my_logs = StudyLog.objects.filter(user=request.user)

    # --- 日別の解いた問題数（折れ線グラフ用） ---
    daily_qs = (
        my_logs
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(
            daily_solves=Sum('solve_count'),
            daily_videos=Sum('study_video_count'),
            daily_time=Sum('study_time'),
        )
        .order_by('date')
    )
    daily_labels = []
    daily_solves = []
    daily_videos = []
    cumulative_solves = 0
    cumulative_solves_list = []

    for d in daily_qs:
        daily_labels.append(d['date'].strftime('%m/%d'))
        daily_solves.append(d['daily_solves'] or 0)
        daily_videos.append(d['daily_videos'] or 0)
        cumulative_solves += (d['daily_solves'] or 0)
        cumulative_solves_list.append(cumulative_solves)

    # --- 科目別の問題数（横棒グラフ用） ---
    subjects = Subject.objects.all().order_by('code')
    subject_labels = []
    subject_solved = []
    subject_totals = []

    for s in subjects:
        subject_labels.append(s.name)
        solved = my_logs.filter(subject=s).aggregate(t=Sum('solve_count'))['t'] or 0
        subject_solved.append(solved)
        subject_totals.append(s.total_question_count)

    # --- サマリー ---
    total_solved = sum(subject_solved)
    total_questions = sum(subject_totals)
    total_xp = calc_total_xp(my_logs)
    total_level = int(total_xp / 500) + 1
    next_level_xp = total_level * 500

    context = {
        'daily_labels': json.dumps(daily_labels),
        'daily_solves': json.dumps(daily_solves),
        'daily_videos': json.dumps(daily_videos),
        'cumulative_solves': json.dumps(cumulative_solves_list),
        'subject_labels': json.dumps(subject_labels),
        'subject_solved': json.dumps(subject_solved),
        'subject_totals': json.dumps(subject_totals),
        'total_solved': total_solved,
        'total_questions': total_questions,
        'total_xp': total_xp,
        'total_level': total_level,
        'next_level_xp': next_level_xp,
    }
    return render(request, "logs/stats.html", context)
