from django.contrib import admin
from import_export.admin import ImportExportModelAdmin # ← インポート機能を使うためのクラス
from .models import Subject, StudyLog

# 【変更】ただの ModelAdmin ではなく ImportExportModelAdmin を使うように変更
@admin.register(Subject)
class SubjectAdmin(ImportExportModelAdmin):
    # 一覧に表示する項目
    list_display = ('code', 'name', 'total_video_count', 'total_question_count')
    # インポート時にキーとして使う項目（IDの代わりにコードで重複判定など）
    # 今回はシンプルにデフォルト設定でOK

# StudyLogはそのまま（手入力がメインなので）
class StudyLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'study_type', 'study_video_count', 'created_at')

admin.site.register(StudyLog, StudyLogAdmin)