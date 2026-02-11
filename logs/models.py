from django.db import models
from django.conf import settings


class Subject(models.Model):
    name = models.CharField(max_length=50, verbose_name="科目名")
    code = models.CharField(max_length=5, verbose_name="科目コード")

    # 【変更】時間の代わりに「本数」でゴールを設定
    total_video_count = models.PositiveIntegerField(
        default=0, verbose_name="動画総本数(本)"
    )
    total_question_count = models.PositiveIntegerField(
        default=0, verbose_name="問題総数(問)"
    )

    image = models.ImageField(
        upload_to="enemies/", null=True, blank=True, verbose_name="敵キャラ画像"
    )

    def __str__(self):
        return f"{self.code}: {self.name}"


class StudyLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="科目")

    STUDY_TYPE_CHOICES = (
        ("QA", "Q-Assist"),
        ("QB", "Question Bank"),
        ("OTHER", "その他"),
    )
    study_type = models.CharField(
        max_length=10, choices=STUDY_TYPE_CHOICES, verbose_name="教材"
    )

    # 【追加】今回消化した動画の本数
    study_video_count = models.PositiveIntegerField(
        default=0, verbose_name="見た動画(本)"
    )

    # 学習時間は「レベル計算用」として一応残しておきます（入力は任意でOK）
    study_time = models.PositiveIntegerField(default=0, verbose_name="学習時間(分)")
    solve_count = models.PositiveIntegerField(default=0, verbose_name="演習問題数")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} ({self.created_at.strftime('%Y/%m/%d')})"
