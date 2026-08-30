import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { UploadCloud, FileText, Plus, BookOpen, BrainCircuit, Trash2, CheckCircle2 } from 'lucide-react';
import UploadNotesModal from '../components/UploadNotesModal';
import AnalysisReportModal from '../components/AnalysisReportModal';

const API_BASE_URL = 'http://localhost:8000/api';

export default function Upload() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportData, setReportData] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/notes/`);
      setNotes(res.data);
    } catch (err) {
      console.error('Error fetching notes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteNote = async (id) => {
    if (!window.confirm('Are you sure you want to delete this note?')) return;
    try {
      await axios.delete(`${API_BASE_URL}/notes/${id}/`);
      setNotes(notes.filter(n => n.id !== id));
    } catch (err) {
      console.error('Delete note error:', err);
    }
  };

  const handleAnalysisSuccess = (resultData) => {
    setReportData(resultData);
    setIsReportModalOpen(true);
    fetchNotes();
  };

  return (
    <div className="upload-notes-page">
      <header className="page-header" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title" style={{ fontSize: '1.75rem', fontWeight: 800 }}>
            Upload Notes
          </h1>
          <p className="page-subtitle" style={{ color: 'var(--text-secondary)' }}>
            Upload study documents (PDF, DOCX, Images) and analyze them against your course syllabus.
          </p>
        </div>

        <button
          onClick={() => setIsUploadModalOpen(true)}
          className="btn-new"
          style={{ padding: '0.75rem 1.4rem', fontSize: '0.9rem' }}
        >
          <Plus size={18} /> Upload Notes
        </button>
      </header>

      {/* Uploaded Notes List / Clean Empty State */}
      <div className="dash-card">
        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1.25rem' }}>
          Uploaded Notes ({notes.length})
        </h3>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
            Loading study notes...
          </div>
        ) : notes.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {notes.map((note) => (
              <div 
                key={note.id}
                style={{
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  background: '#ffffff'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div className="stat-icon blue" style={{ width: '42px', height: '42px', marginBottom: 0 }}>
                    <FileText size={20} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                      {note.original_filename}
                    </h4>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: '1rem', marginTop: '2px' }}>
                      <span>Uploaded: {new Date(note.upload_timestamp).toLocaleDateString()}</span>
                      <span>Format: {note.file_type?.toUpperCase()}</span>
                      <span>Status: <strong style={{ color: '#047857' }}>{note.status}</strong></span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <button
                    onClick={() => setIsUploadModalOpen(true)}
                    className="btn-new"
                    style={{ background: 'var(--bg-card-subtle)', color: 'var(--primary-accent)', border: '1px solid var(--border-subtle)', padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
                  >
                    <BrainCircuit size={15} /> Analyze vs Syllabus
                  </button>
                  <button
                    onClick={() => handleDeleteNote(note.id)}
                    style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '0.4rem' }}
                    title="Delete Note"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Clean Initial Empty State */
          <div style={{ textAlign: 'center', padding: '3.5rem 1.5rem', background: 'var(--bg-card-subtle)', borderRadius: 'var(--radius-md)', border: '2px dashed #cbd5e1' }}>
            <div className="stat-icon blue" style={{ margin: '0 auto 1rem auto', width: '52px', height: '52px' }}>
              <UploadCloud size={26} />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              No notes uploaded yet.
            </h3>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '420px', margin: '0.5rem auto 1.5rem auto', fontSize: '0.85rem' }}>
              Upload your study notes (PDF, DOCX, Images) to analyze coverage against your saved syllabus sections.
            </p>
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="btn-new"
              style={{ padding: '0.75rem 1.75rem', fontSize: '0.9rem' }}
            >
              <Plus size={18} /> Upload Notes
            </button>
          </div>
        )}
      </div>

      {/* Upload Notes Modal */}
      <UploadNotesModal 
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onAnalysisSuccess={handleAnalysisSuccess}
        onNavigateToSyllabus={() => navigate('/syllabus')}
      />

      {/* Analysis Result Pop-up Modal */}
      <AnalysisReportModal 
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        data={reportData}
      />
    </div>
  );
}
