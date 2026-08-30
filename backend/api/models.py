from django.db import models
import os

class Note(models.Model):
    """
    Model representing an uploaded study note / document for AI Quality Analysis.
    """
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    original_filename = models.CharField(max_length=255, blank=True)
    uploaded_file = models.FileField(upload_to='notes/')
    file_type = models.CharField(max_length=10)  # e.g., pdf, jpg, jpeg, png
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, default="")
    overall_score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')

    # Universal Education Metadata (Flexible across School, College, Exams & Self-Learning)
    education_level = models.CharField(max_length=100, blank=True, default="", help_text="Class 3, Class 12, MBBS, B.Tech, UPSC, Self-Learner")
    subject_domain = models.CharField(max_length=100, blank=True, default="", help_text="Physics, Anatomy, Accounting, DSA, Constitutional Law, EVS")
    topic = models.CharField(max_length=200, blank=True, default="")



    def save(self, *args, **kwargs):
        if self.uploaded_file and not self.file_type:
            ext = os.path.splitext(self.uploaded_file.name)[1].lower().replace('.', '')
            self.file_type = ext
        if self.uploaded_file and not self.original_filename:
            self.original_filename = os.path.basename(self.uploaded_file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Note {self.id} - {self.original_filename} ({self.file_type})"

    class Meta:
        ordering = ['-upload_timestamp']


class Syllabus(models.Model):
    """
    Model representing an uploaded educational syllabus (PDF, DOCX, JPG, PNG).
    Stores extracted text and parsed hierarchical units/modules/topics.
    """
    title = models.CharField(max_length=255, default="Untitled Syllabus")
    original_filename = models.CharField(max_length=255, blank=True)
    uploaded_file = models.FileField(upload_to='syllabi/')
    file_type = models.CharField(max_length=10)  # e.g., pdf, docx, jpg, jpeg, png
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, default="")
    parsed_units = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        if self.uploaded_file and not self.file_type:
            ext = os.path.splitext(self.uploaded_file.name)[1].lower().replace('.', '')
            self.file_type = ext
        if self.uploaded_file and not self.original_filename:
            self.original_filename = os.path.basename(self.uploaded_file.name)
        if not self.title or self.title == "Untitled Syllabus":
            clean_title = os.path.splitext(self.original_filename)[0].replace('_', ' ').replace('-', ' ').title()
            self.title = clean_title if clean_title else "Untitled Syllabus"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Syllabus {self.id} - {self.title} ({self.file_type})"

    class Meta:
        ordering = ['-upload_timestamp']


