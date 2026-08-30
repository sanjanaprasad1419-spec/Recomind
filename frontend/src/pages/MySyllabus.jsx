import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BookOpen, UploadCloud, FileText, Trash2, CheckCircle2, ChevronRight, Loader2 } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

export default function MySyllabus() {
  const [syllabi, setSyllabi] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [titleInput, setTitleInput] = useState('');
  const [message, setMessage] = useState('');
  const [expandedSyllabusId, setExpandedSyllabusId] = useState(null);

  useEffect(() => {
    fetchSyllabi();
  }, []);

  const fetchSyllabi = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/syllabus/`);
      setSyllabi(res.data);
    } catch (err) {
      console.error('Error fetching syllabi:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setSelectedFile(f);
      if (!titleInput) {
        const cleanName = f.name.substring(0, f.name.lastIndexOf('.')) || f.name;
        setTitleInput(cleanName.replace(/[_]/g, ' ').replace(/[-]/g, ' '));
      }
    }
  };

  const handleUploadSyllabus = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setMessage('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('title', titleInput);

    try {
      await axios.post(`${API_BASE_URL}/syllabus/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setMessage('Syllabus uploaded and parsed successfully!');
      setSelectedFile(null);
      setTitleInput('');
      fetchSyllabi();
    } catch (err) {
      console.error('Syllabus upload error:', err);
      setMessage(err.response?.data?.file?.[0] || 'Failed to upload syllabus document.');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteSyllabus = async (id) => {
    if (!window.confirm('Are you sure you want to delete this syllabus?')) return;
    try {
      await axios.delete(`${API_BASE_URL}/syllabus/${id}/`);
      setSyllabi(syllabi.filter(s => s.id !== id));
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  return (
    <div className="my-syllabus-page">
      <header className="page-header" style={{ marginBottom: '1.5rem' }}>
        <h1 className="page-title" style={{ fontSize: '1.75rem', fontWeight: 800 }}>
          My Syllabus Repository
        </h1>
        <p className="page-subtitle" style={{ color: 'var(--text-secondary)' }}>
          Upload and manage your course syllabi (PDF, DOCX, JPG, PNG). RecoMind automatically extracts topics and chapters.
        </p>
      </header>

      {/* Upload Syllabus Form */}
      <div className="dash-card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <UploadCloud size={20} style={{ color: 'var(--primary-accent)' }} /> Upload New Syllabus
        </h3>

        <form onSubmit={handleUploadSyllabus} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.4rem', display: 'block' }}>
              Syllabus Title (e.g. Physics 2026-27)
            </label>
            <input
              type="text"
              value={titleInput}
              onChange={(e) => setTitleInput(e.target.value)}
              placeholder="e.g. Class 12 Physics, B.Tech Operating Systems, UPSC Polity"
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.9rem',
                outline: 'none',
                background: 'var(--bg-card-subtle)'
              }}
            />
          </div>

          <div 
            style={{
              border: '2px dashed #cbd5e1',
              borderRadius: 'var(--radius-md)',
              padding: '1.5rem',
              textAlign: 'center',
              background: 'var(--bg-card-subtle)',
              cursor: 'pointer'
            }}
          >
            <input 
              type="file" 
              id="syllabusFileInput" 
              onChange={handleFileChange} 
              style={{ display: 'none' }}
              accept=".pdf,.docx,.doc,image/*"
            />
            <label htmlFor="syllabusFileInput" style={{ cursor: 'pointer', display: 'inline-block' }}>
              <div style={{ color: 'var(--primary-accent)', fontWeight: 700, fontSize: '0.9rem' }}>
                {selectedFile ? `Selected: ${selectedFile.name}` : 'Click to Browse Syllabus File (PDF, DOCX, Image)'}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Max file size: 20MB
              </div>
            </label>
          </div>

          {message && (
            <div style={{ padding: '0.75rem', background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#047857', borderRadius: 'var(--radius-md)', fontSize: '0.85rem' }}>
              {message}
            </div>
          )}

          <button
            type="submit"
            className="btn-new"
            disabled={!selectedFile || uploading}
            style={{ alignSelf: 'flex-start', padding: '0.75rem 1.75rem', fontSize: '0.9rem', cursor: (!selectedFile || uploading) ? 'not-allowed' : 'pointer' }}
          >
            {uploading ? (
              <>
                <Loader2 size={16} className="spin" style={{ animation: 'spin 1s linear infinite' }} /> Extracting & Parsing Syllabus...
              </>
            ) : (
              <>
                <BookOpen size={16} /> Upload & Save Syllabus
              </>
            )}
          </button>
        </form>
      </div>

      {/* Saved Syllabi List */}
      <div className="dash-card">
        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1.25rem' }}>
          Saved Syllabi ({syllabi.length})
        </h3>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading syllabi repository...</div>
        ) : syllabi.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {syllabi.map((syl) => (
              <div 
                key={syl.id} 
                style={{ 
                  border: '1px solid var(--border-subtle)', 
                  borderRadius: 'var(--radius-md)', 
                  padding: '1.25rem',
                  background: '#ffffff'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <div className="stat-icon purple" style={{ width: '42px', height: '42px', marginBottom: 0 }}>
                      <BookOpen size={20} />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>{syl.title}</h4>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: '1rem', marginTop: '2px' }}>
                        <span>Uploaded: {new Date(syl.upload_timestamp).toLocaleDateString()}</span>
                        <span>Format: {syl.file_type?.toUpperCase()}</span>
                        <span>Chapters: {syl.units_count || 0}</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <button
                      onClick={() => setExpandedSyllabusId(expandedSyllabusId === syl.id ? null : syl.id)}
                      style={{ background: 'none', border: '1px solid var(--border-subtle)', padding: '0.4rem 0.75rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}
                    >
                      {expandedSyllabusId === syl.id ? 'Hide Chapters' : 'View Chapters'}
                    </button>
                    <button
                      onClick={() => handleDeleteSyllabus(syl.id)}
                      style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '0.4rem' }}
                      title="Delete Syllabus"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>

                {/* Expanded Parsed Units View */}
                {expandedSyllabusId === syl.id && (
                  <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px dashed var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.65rem', color: 'var(--primary-accent)' }}>
                      Extracted Chapters ({syl.parsed_units?.length || 0}):
                    </h5>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {syl.parsed_units?.map((unit, idx) => (
                        <div key={idx} style={{ background: 'var(--bg-card-subtle)', padding: '0.65rem 0.85rem', borderRadius: '6px' }}>
                          <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{unit.title}</strong>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                            Topics: {unit.topics?.join(', ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem 1.5rem', background: 'var(--bg-card-subtle)', borderRadius: 'var(--radius-md)', border: '2px dashed #cbd5e1' }}>
            <div className="stat-icon purple" style={{ margin: '0 auto 1rem auto', width: '52px', height: '52px' }}>
              <BookOpen size={26} />
            </div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              No syllabus uploaded yet.
            </h3>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', margin: '0.5rem auto 1.25rem auto', fontSize: '0.85rem' }}>
              Upload your course syllabus (PDF, DOCX, Images) to automatically extract chapters, units, and subtopics.
            </p>
            <label htmlFor="syllabusFileInput" className="btn-new" style={{ padding: '0.75rem 1.5rem', fontSize: '0.85rem', cursor: 'pointer', display: 'inline-flex' }}>
              + Upload Syllabus
            </label>
          </div>
        )}

      </div>
    </div>
  );
}
