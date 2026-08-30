from django.urls import path
from .views import (
    health_check, 
    upload_note, NoteListAPIView, NoteDetailAPIView, 
    upload_syllabus, SyllabusListAPIView, SyllabusDetailAPIView, syllabus_sections_view,
    predict_domain_view, analyze_notes_view, enhance_notes_view, generate_topic_notes_view,
    download_pdf_report_view
)



urlpatterns = [
    path('health/', health_check, name='health-check'),
    
    # Note Management Endpoints
    path('notes/upload/', upload_note, name='note-upload'),
    path('notes/', NoteListAPIView.as_view(), name='note-list'),
    path('notes/<int:pk>/', NoteDetailAPIView.as_view(), name='note-detail'),

    # Syllabus Management Endpoints
    path('syllabus/upload/', upload_syllabus, name='syllabus-upload'),
    path('syllabus/', SyllabusListAPIView.as_view(), name='syllabus-list'),
    path('syllabus/<int:pk>/', SyllabusDetailAPIView.as_view(), name='syllabus-detail'),
    path('syllabus/<int:pk>/sections/', syllabus_sections_view, name='syllabus-sections'),


    # ML Analysis, AI Enhancement & PDF Report Endpoints
    path('predict-domain/', predict_domain_view, name='predict-domain'),
    path('analyze-notes/', analyze_notes_view, name='analyze-notes'),
    path('enhance-notes/', enhance_notes_view, name='enhance-notes'),
    path('generate-topic-notes/', generate_topic_notes_view, name='generate-topic-notes'),
    path('analysis/download-pdf/', download_pdf_report_view, name='download-pdf'),

]
