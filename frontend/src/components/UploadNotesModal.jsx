import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, UploadCloud, File, BookOpen, BrainCircuit, Loader2, AlertCircle, Plus } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

export default function UploadNotesModal({ isOpen, onClose, onAnalysisSuccess, onNavigateToSyllabus }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [syllabi, setSyllabi] = useState([]);
  const [selectedSyllabusId, setSelectedSyllabusId] = useState('');
  const [sections, setSections] = useState([]);
  const [selectedUnitId, setSelectedUnitId] = useState('');

  const [loadingSyllabi, setLoadingSyllabi] = useState(false);
  const [loadingSections, setLoadingSections] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetchSyllabi();
      setSelectedFile(null);
      setError('');
    }
  }, [isOpen]);

  const fetchSyllabi = async () => {
    setLoadingSyllabi(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/syllabus/`);
      setSyllabi(res.data);
      if (res.data.length > 0) {
        const firstId = res.data[0].id;
        setSelectedSyllabusId(firstId);
        fetchSections(firstId);
      }
    } catch (err) {
      console.error('Error fetching syllabi:', err);
    } finally {
      setLoadingSyllabi(false);
    }
  };

  const fetchSections = async (sylId) => {
    if (!sylId) return;
    setLoadingSections(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/syllabus/${sylId}/sections/`);
      const uList = res.data.sections || [];
      setSections(uList);
      if (uList.length > 0) {
        setSelectedUnitId(uList[0].id || uList[0].unit_id);
      } else {

        setSelectedUnitId('');
      }
    } catch (err) {
      console.error('Error fetching syllabus sections:', err);
      setSections([]);
      setError('Could not load syllabus chapters. Please try again.');
    } finally {
      setLoadingSections(false);
    }
  };

  const handleSyllabusChange = (sylId) => {
    setSelectedSyllabusId(sylId);
    fetchSections(sylId);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadAndAnalyze = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a study notes file to upload.');
      return;
    }
    if (!selectedSyllabusId) {
      setError('Please select a saved syllabus from the dropdown.');
      return;
    }
    if (!selectedUnitId) {
      setError('No chapters were detected for this syllabus. Upload a syllabus with chapter headings before analysis.');
      return;
    }

    setAnalyzing(true);
    setError('');

    try {
      // Step 1: Reading notes...
      setAnalysisStep('Reading your notes document...');
      const formData = new FormData();
      formData.append('file', selectedFile);

      const noteUploadRes = await axios.post(`${API_BASE_URL}/notes/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const noteId = noteUploadRes.data.note.id;

      // Step 2: Checking syllabus coverage...
      setAnalysisStep('Checking syllabus coverage & parsing topics...');
      
      // Step 3: Analyzing topics...
      setAnalysisStep('Analyzing topics with Sentence Transformer ML embeddings...');

      const analysisPayload = {
        note_id: noteId,
        syllabus_id: Number(selectedSyllabusId),
        unit_id: selectedUnitId
      };

      const analysisRes = await axios.post(`${API_BASE_URL}/analyze-notes/`, analysisPayload);

      // Step 4: Preparing recommendations...
      setAnalysisStep('Preparing personalized study recommendations...');
      
      onAnalysisSuccess(analysisRes.data);
      onClose();
    } catch (err) {
      console.error('Upload & Analyze Error:', err);
      setError(err.response?.data?.error || err.response?.data?.file?.[0] || 'Failed to analyze notes against syllabus.');
    } finally {
      setAnalyzing(false);
      setAnalysisStep('');
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.55)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '1.5rem'
      }}
    >
      <div 
        style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          width: '100%',
          maxWidth: '580px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          overflow: 'hidden',
          animation: 'fadeIn 0.2s ease-out'
        }}
      >
        {/* Modal Header */}
        <div 
          style={{
            padding: '1.25rem 1.75rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            justify: 'space-between',
            alignItems: 'center',
            background: 'var(--bg-card-subtle)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <UploadCloud size={20} style={{ color: 'var(--primary-accent)' }} />
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Upload Notes
            </h2>
          </div>
          <button 
            onClick={onClose}
            disabled={analyzing}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '0.5rem' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleUploadAndAnalyze} style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Step 1: Upload Notes File */}
          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.4rem', display: 'block' }}>
              1. Choose Study Notes File:
            </label>
            <div 
              style={{
                border: '2px dashed #cbd5e1',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
                textAlign: 'center',
                background: 'var(--bg-card-subtle)',
                cursor: 'pointer'
              }}
            >
              <input 
                type="file" 
                id="modalNoteInput" 
                onChange={handleFileChange}
                style={{ display: 'none' }}
                accept=".pdf,.docx,.doc,image/*"
              />
              <label htmlFor="modalNoteInput" style={{ cursor: 'pointer', display: 'inline-block' }}>
                <div style={{ color: 'var(--primary-accent)', fontWeight: 700, fontSize: '0.9rem' }}>
                  {selectedFile ? `Selected: ${selectedFile.name}` : 'Click to Browse Notes File (PDF, DOCX, Images)'}
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.2rem' }}>
                  Max size: 20MB
                </div>
              </label>
            </div>
          </div>

          {/* Step 2: Select Syllabus Dropdown */}
          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.4rem', display: 'block' }}>
              2. Select Syllabus:
            </label>
            {loadingSyllabi ? (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Loading syllabi repository...</div>
            ) : syllabi.length > 0 ? (
              <select
                value={selectedSyllabusId}
                onChange={(e) => handleSyllabusChange(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.9rem',
                  outline: 'none',
                  background: 'var(--bg-card-subtle)',
                  fontWeight: 600
                }}
              >
                {syllabi.map((syl) => (
                  <option key={syl.id} value={syl.id}>
                    {syl.title} ({syl.units_count || 0} chapters)
                  </option>
                ))}
              </select>
            ) : (
              <div style={{ padding: '0.85rem', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: '#b45309' }}>No syllabus available. Upload a syllabus first.</span>
                <button
                  type="button"
                  onClick={() => { onClose(); onNavigateToSyllabus(); }}
                  style={{ background: '#f59e0b', color: '#ffffff', border: 'none', padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  Upload Syllabus
                </button>
              </div>
            )}
          </div>

          {/* Step 3: Select Chapter Dropdown */}
          {selectedSyllabusId && (
            <div>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.4rem', display: 'block' }}>
                3. Select Chapter:
              </label>
              {loadingSections ? (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Fetching parsed chapters...</div>
              ) : (
                <select
                  value={selectedUnitId}
                  onChange={(e) => setSelectedUnitId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.9rem',
                    outline: 'none',
                    background: 'var(--bg-card-subtle)',
                    fontWeight: 600
                  }}
                >
                  {sections.length > 0 ? (
                    sections.map((u) => (
                      <option key={u.id || u.unit_id} value={u.id || u.unit_id}>
                        {u.part ? `${u.part} \u2014 ${u.title}` : u.title}
                      </option>
                    ))
                  ) : (
                    <option value="">No chapters detected in this syllabus</option>
                  )}

                </select>
              )}
            </div>
          )}


          {/* Error Message */}
          {error && (
            <div style={{ padding: '0.75rem', background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', borderRadius: 'var(--radius-md)', fontSize: '0.85rem' }}>
              {error}
            </div>
          )}

          {/* Loading Progress State */}
          {analyzing && (
            <div style={{ padding: '0.85rem', background: '#e0e7ff', border: '1px solid #c7d2fe', borderRadius: 'var(--radius-md)', color: '#3730a3', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Loader2 size={16} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
              <span>{analysisStep || 'Analyzing notes...'}</span>
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={analyzing}
              style={{ padding: '0.65rem 1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', background: '#ffffff', color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={analyzing || !selectedFile || !selectedSyllabusId || !selectedUnitId}
              className="btn-new"
              style={{ padding: '0.65rem 1.4rem', fontSize: '0.85rem', cursor: (analyzing || !selectedFile || !selectedSyllabusId || !selectedUnitId) ? 'not-allowed' : 'pointer' }}
            >
              <BrainCircuit size={16} /> Upload & Analyze Notes
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}
