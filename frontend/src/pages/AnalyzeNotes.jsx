import React, { useState } from 'react';
import axios from 'axios';
import { 
  BrainCircuit, FileText, BookOpen, Loader2, UploadCloud, AlertCircle
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

const SAMPLE_SYLLABUS = `Chapter 1: Electric Charges and Fields
- Coulomb's Law and Electric Force
- Electric Field & Field Lines
- Electric Dipole & Field Due to Dipole
- Gauss's Law and Electric Flux
- Field due to Uniformly Charged Thin Spherical Shell`;

const SAMPLE_NOTES = `Coulomb's Law states that force between two point charges q1 and q2 is proportional to q1*q2/r^2.
Electric field is defined as force per unit charge E = F/q.
Electric dipole consists of two equal and opposite charges separated by distance 2a.`;

export default function AnalyzeNotes() {
  const [syllabusFile, setSyllabusFile] = useState(null);
  const [noteFile, setNoteFile] = useState(null);
  const [syllabusText, setSyllabusText] = useState(SAMPLE_SYLLABUS);
  const [noteText, setNoteText] = useState(SAMPLE_NOTES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');
    setAnalysisResult(null);

    try {
      let response;
      if (syllabusFile || noteFile) {
        const formData = new FormData();
        if (syllabusFile) {
          formData.append('syllabus_file', syllabusFile);
        } else {
          formData.append('syllabus_text', syllabusText);
        }

        if (noteFile) {
          formData.append('note_file', noteFile);
        } else {
          formData.append('note_text', noteText);
        }

        response = await axios.post(`${API_BASE_URL}/analyze-notes/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        if (!noteText.trim() || !syllabusText.trim()) {
          setError('Please provide both study notes and syllabus topics (or upload files).');
          setLoading(false);
          return;
        }
        response = await axios.post(`${API_BASE_URL}/analyze-notes/`, {
          note_text: noteText,
          syllabus_text: syllabusText,
        });
      }

      setAnalysisResult(response.data);
    } catch (err) {
      console.error('Analysis error:', err);
      const errMsg = err.response?.data?.error || err.response?.data?.details || 'Failed to connect to backend analysis API.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analyze-notes-page" style={{ maxWidth: '900px', margin: '0 auto' }}>
      <header className="page-header" style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
        <h1 className="page-title" style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          RecoMind Notes Coverage Analysis
        </h1>
        <p className="page-subtitle" style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginTop: '0.25rem' }}>
          Upload your 1-Chapter Syllabus and Student Notes to evaluate semantic topic coverage.
        </p>
      </header>

      {/* Input Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
        
        {/* STEP 1: Syllabus Upload / Input */}
        <div className="dash-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <label style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BookOpen size={18} style={{ color: 'var(--primary-accent)' }} /> 1. Syllabus PDF (1 Chapter)
            </label>
            <button 
              type="button" 
              onClick={() => { setSyllabusFile(null); setSyllabusText(SAMPLE_SYLLABUS); }}
              style={{ background: 'none', border: 'none', color: 'var(--primary-accent)', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600 }}
            >
              Reset Sample
            </button>
          </div>

          <div style={{ border: '2px dashed #cbd5e1', borderRadius: 'var(--radius-md)', padding: '1rem', textAlign: 'center', background: 'var(--bg-card-subtle)', marginBottom: '0.75rem' }}>
            <input 
              type="file" 
              id="syllabusFileInput" 
              accept=".pdf,.docx,.doc,image/*" 
              onChange={(e) => { if (e.target.files?.[0]) setSyllabusFile(e.target.files[0]); }} 
              style={{ display: 'none' }} 
            />
            <label htmlFor="syllabusFileInput" style={{ cursor: 'pointer', display: 'block' }}>
              <UploadCloud size={22} style={{ color: 'var(--primary-accent)', margin: '0 auto 0.25rem auto' }} />
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--primary-accent)' }}>
                {syllabusFile ? syllabusFile.name : 'Upload Syllabus PDF'}
              </div>
            </label>
          </div>

          <textarea
            rows={5}
            value={syllabusText}
            onChange={(e) => { setSyllabusText(e.target.value); setSyllabusFile(null); }}
            placeholder="Or paste 1-chapter syllabus topics here..."
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontFamily: 'inherit',
              fontSize: '0.85rem',
              outline: 'none',
              resize: 'vertical',
              background: 'var(--bg-card-subtle)'
            }}
          />
        </div>

        {/* STEP 2: Notes Upload / Input */}
        <div className="dash-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <label style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={18} style={{ color: '#047857' }} /> 2. Student Notes PDF / Image
            </label>
            <button 
              type="button" 
              onClick={() => { setNoteFile(null); setNoteText(SAMPLE_NOTES); }}
              style={{ background: 'none', border: 'none', color: '#047857', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600 }}
            >
              Reset Sample
            </button>
          </div>

          <div style={{ border: '2px dashed #cbd5e1', borderRadius: 'var(--radius-md)', padding: '1rem', textAlign: 'center', background: 'var(--bg-card-subtle)', marginBottom: '0.75rem' }}>
            <input 
              type="file" 
              id="noteFileInput" 
              accept=".pdf,.docx,.doc,image/*" 
              onChange={(e) => { if (e.target.files?.[0]) setNoteFile(e.target.files[0]); }} 
              style={{ display: 'none' }} 
            />
            <label htmlFor="noteFileInput" style={{ cursor: 'pointer', display: 'block' }}>
              <UploadCloud size={22} style={{ color: '#047857', margin: '0 auto 0.25rem auto' }} />
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#047857' }}>
                {noteFile ? noteFile.name : 'Upload Student Notes File'}
              </div>
            </label>
          </div>

          <textarea
            rows={5}
            value={noteText}
            onChange={(e) => { setNoteText(e.target.value); setNoteFile(null); }}
            placeholder="Or paste student notes text here..."
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontFamily: 'inherit',
              fontSize: '0.85rem',
              outline: 'none',
              resize: 'vertical',
              background: 'var(--bg-card-subtle)'
            }}
          />
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div style={{ padding: '0.85rem 1.25rem', background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.9rem', textAlign: 'center' }}>
          {error}
        </div>
      )}

      {/* STEP 3: Analyze Notes Button */}
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="btn-new"
          style={{ padding: '0.9rem 2.5rem', fontSize: '1.05rem', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? (
            <>
              <Loader2 size={20} className="spin" style={{ animation: 'spin 1s linear infinite' }} /> OCR Extracting & Analyzing...
            </>
          ) : (
            <>
              <BrainCircuit size={22} /> Analyze Notes
            </>
          )}
        </button>
      </div>

      {/* STEP 5: FINAL OUTPUT DISPLAY ONLY */}
      {analysisResult && (
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1rem' }}>
          <div 
            className="dash-card" 
            style={{ 
              width: '100%', 
              maxWidth: '520px', 
              padding: '2.5rem 2rem', 
              borderRadius: 'var(--radius-lg, 16px)',
              background: '#ffffff',
              border: '1px solid var(--border-subtle, #e2e8f0)',
              boxShadow: '0 10px 30px -5px rgba(0, 0, 0, 0.08)'
            }}
          >
            {/* NOTES COVERAGE */}
            <div style={{ textAlign: 'center', marginBottom: '2rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 800, letterSpacing: '0.08em', color: 'var(--text-secondary, #64748b)', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                NOTES COVERAGE
              </div>
              <div style={{ fontSize: '4.5rem', fontWeight: 900, lineHeight: 1, color: 'var(--primary-accent, #4361ee)' }}>
                {analysisResult.coverage_percentage}%
              </div>
            </div>

            {/* WEAK / MISSING TOPICS */}
            <div>
              <div style={{ fontSize: '0.9rem', fontWeight: 800, letterSpacing: '0.05em', color: '#b91c1c', textTransform: 'uppercase', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={18} /> WEAK / MISSING TOPICS
              </div>

              {analysisResult.weak_topics && analysisResult.weak_topics.length > 0 ? (
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                  {analysisResult.weak_topics.map((topic, idx) => (
                    <li 
                      key={idx} 
                      style={{ 
                        fontSize: '0.95rem', 
                        fontWeight: 600, 
                        color: 'var(--text-primary)', 
                        background: '#fef2f2', 
                        border: '1px solid #fecaca', 
                        padding: '0.65rem 1rem', 
                        borderRadius: 'var(--radius-md)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}
                    >
                      <span style={{ color: '#b91c1c', fontWeight: 800 }}>•</span> {topic}
                    </li>
                  ))}
                </ul>
              ) : (
                <div style={{ padding: '0.85rem 1rem', background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#047857', borderRadius: 'var(--radius-md)', fontWeight: 700, fontSize: '0.9rem', textAlign: 'center' }}>
                  ✨ Excellent! All syllabus topics are well covered in your notes.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

