from django.shortcuts import render, redirect
from django.db.models import Sum
from .forms import StudyLogForm
from .models import StudyLog, Subject

def record_quest(request):
    if request.method == 'POST':
        form = StudyLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user_id = 1 
            log.save()
            return redirect('record_quest')
    else:
        form = StudyLogForm()

    # 全科目のデータを取得
    subjects = Subject.objects.all()
    subject_status_list = []

    # 全体のレベル計算用（時間は引き続き使う）
    total_minutes = StudyLog.objects.aggregate(Sum('study_time'))['study_time__sum'] or 0
    total_level = int(total_minutes / 60) + 1

    for subject in subjects:
        logs = StudyLog.objects.filter(subject=subject)
        
        # 【変更】集計対象を「動画本数」に変更
        current_videos = logs.aggregate(Sum('study_video_count'))['study_video_count__sum'] or 0
        current_questions = logs.aggregate(Sum('solve_count'))['solve_count__sum'] or 0
        
        # 進捗率計算：(見た本数 / 総本数) * 100
        if subject.total_video_count > 0:
            video_progress = int((current_videos / subject.total_video_count) * 100)
        else:
            video_progress = 0

        subject_status_list.append({
            'name': subject.name,
            'current_val': current_videos,      # 現在の本数
            'total_val': subject.total_video_count, # 目標本数
            'video_progress': min(video_progress, 100),
        })

    context = {
        'form': form,
        'subject_status_list': subject_status_list,
        'total_level': total_level,
    }

    return render(request, 'logs/record.html', context)