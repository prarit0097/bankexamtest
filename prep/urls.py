from django.urls import path

from prep import views


app_name = "prep"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("admin-panel/", views.AdminPanelView.as_view(), name="admin-panel"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("start-test/", views.StartTestView.as_view(), name="start-test"),
    path("sessions/<int:pk>/", views.TestSessionDetailView.as_view(), name="session-detail"),
    path("sessions/<int:pk>/submit/", views.SubmitTestView.as_view(), name="submit-test"),
    path("sessions/<int:pk>/result/", views.TestResultView.as_view(), name="result"),
]
