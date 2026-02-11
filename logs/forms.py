from django import forms
from .models import StudyLog

class StudyLogForm(forms.ModelForm):
    class Meta:
        model = StudyLog
        # 'study_video_count' を追加
        fields = ['subject', 'study_type', 'study_video_count', 'solve_count', 'study_time']
        
        labels = {
            'subject': '科目',
            'study_type': '教材',
            'study_video_count': '見た動画(本)', # ← ここがメインになります
            'solve_count': '解いた問題(問)',
            'study_time': '勉強時間(分)', # おまけ
        }