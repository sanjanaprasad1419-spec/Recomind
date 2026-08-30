from django.contrib import admin
from .models import Note

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'file_type', 'upload_timestamp', 'status', 'overall_score')
    list_filter = ('file_type', 'status', 'upload_timestamp')
    search_fields = ('original_filename', 'extracted_text')

