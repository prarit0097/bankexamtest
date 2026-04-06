from django.urls import path

from prep import views


app_name = "prep"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("predicted-papers/", views.PredictedPapersView.as_view(), name="predicted-papers"),
    path("predicted-papers/<int:pk>/", views.PredictedPaperDetailView.as_view(), name="predicted-paper-detail"),
    path("admin-panel/", views.AdminPanelView.as_view(), name="admin-panel"),
    path("admin-panel/content-assets/", views.AdminContentAssetsView.as_view(), name="admin-content-assets"),
    path("admin-panel/questions/", views.AdminQuestionBankView.as_view(), name="admin-question-bank"),
    path("admin-panel/predictions/", views.AdminPredictionSetsView.as_view(), name="admin-predictions"),
    path("admin-panel/test-sessions/", views.AdminTestSessionsView.as_view(), name="admin-test-sessions"),
    path("admin-panel/delivery-logs/", views.AdminDeliveryLogsView.as_view(), name="admin-delivery-logs"),
    path("admin-panel/ingestion-logs/", views.AdminIngestionLogsView.as_view(), name="admin-ingestion-logs"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("start-test/", views.StartTestView.as_view(), name="start-test"),
    path("sessions/<int:pk>/", views.TestSessionDetailView.as_view(), name="session-detail"),
    path("sessions/<int:pk>/submit/", views.SubmitTestView.as_view(), name="submit-test"),
    path("sessions/<int:pk>/result/", views.TestResultView.as_view(), name="result"),
]
