import React, { useState } from 'react';
import axios from 'axios';
import { 
  BrainCircuit, CheckCircle2, AlertTriangle, XCircle, 
  Sparkles, FileText, BookOpen, ArrowRight, Loader2, RefreshCw, Lightbulb 
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

const SAMPLE_SYLLABUS = `1. Cell Membrane Structure & Selective Permeability
2. Mitochondria ATP Cellular Respiration
3. Cell Division Mitosis and Meiosis Stages
4. DNA Replication and Genetics Transcription`;

const SAMPLE_NOTES = `The plasma membrane is a selectively permeable phospholipid bilayer that regulates nutrient transport in and out of cells.
Mitochondria generate ATP energy through the Krebs citric acid cycle and oxidative phosphorylation in cellular respiration.`;

export default function AnalyzeNotes() {
  const [noteText, setNoteText] = useState(SAMPLE_NOTES);
  const [syllabusText, setSyllabusText] = useState(SAMPLE_SYLLABUS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!noteText.trim() || !syllabusText.trim()) {
      setError('Please provide both study notes text and syllabus topics.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/analyze-notes/`, {
        note_text: noteText,
        syllabus_text: syllabusText,
      });

      setAnalysisResult(response.data);
    } catch (err) {
      console.error('Analysis error:', err);
      const errMsg = err.response?.data?.error || err.response?.data?.details || 'Failed to connect to backend ML API.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analyze-notes-page">
      <header className="page-header" style={{ marginBottom: '1.5rem' }}>
        <h1 className="page-title" style={{ fontSize: '1.75rem', fontWeight: 800 }}>
          Semantic Notes & Syllabus Analysis
        </h1>
        <p className="page-subtitle" style={{ color: 'var(--text-secondary)' }}>
          Evaluate study notes against your syllabus using Sentence Transformer embeddings & ML coverage prediction.
        </p>
      </header>

      {/* Input Section */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
        {/* Notes Input Card */}
        <div className="dash-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <label style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={18} style={{ color: 'var(--primary-accent)' }} /> Study Notes Content
            </label>
            <button 
              type="button" 
              onClick={() => setNoteText(SAMPLE_NOTES)}
              style={{ background: 'none', border: 'none', color: 'var(--primary-accent)', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600 }}
            >
              Load Sample Notes
            </button>
          </div>
          <textarea
            rows={7}
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Paste your study notes text here..."
            style={{
              width: '100%',
              padding: '0.85rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontFamily: 'inherit',
              fontSize: '0.9rem',
              outline: 'none',
              resize: 'vertical',
              background: 'var(--bg-card-subtle)'
            }}
          />
        </div>

        {/* Syllabus Input Card */}
        <div className="dash-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <label style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BookOpen size={18} style={{ color: '#8b5cf6' }} /> Syllabus Topics
            </label>
            <button 
              type="button" 
              onClick={() => setSyllabusText(SAMPLE_SYLLABUS)}
              style={{ background: 'none', border: 'none', color: '#8b5cf6', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600 }}
            >
              Load Sample Syllabus
            </button>
          </div>
          <textarea
            rows={7}
            value={syllabusText}
            onChange={(e) => setSyllabusText(e.target.value)}
            placeholder="Paste syllabus topics (one per line or bullet point)..."
            style={{
              width: '100%',
              padding: '0.85rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontFamily: 'inherit',
              fontSize: '0.9rem',
              outline: 'none',
              resize: 'vertical',
              background: 'var(--bg-card-subtle)'
            }}
          />
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div style={{ padding: '0.85rem 1.25rem', background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          {error}
        </div>
      )}

      {/* Analyze Button */}
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="btn-new"
          style={{ padding: '0.85rem 2.2rem', fontSize: '1rem', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? (
            <>
              <Loader2 size={18} className="spin" style={{ animation: 'spin 1s linear infinite' }} /> Analyzing Notes Semantics...
            </>
          ) : (
            <>
              <BrainCircuit size={20} /> Analyze Notes Against Syllabus
            </>
          )}
        </button>
      </div>

      {/* Analysis Results Display */}
      {analysisResult && (
        <div className="results-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Metrics Top Header Row */}
          <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
            <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div className="stat-icon blue" style={{ background: '#e0e7ff', color: '#4361ee', marginBottom: 0 }}>
                <BrainCircuit size={24} />
              </div>
              <div>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {analysisResult.coverage_percentage}%
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Overall Syllabus Coverage
                </div>
              </div>
            </div>

            <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div className="stat-icon purple" style={{ background: '#f3e8ff', color: '#9333ea', marginBottom: 0 }}>
                <Sparkles size={24} />
              </div>
              <div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {analysisResult.domain}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Predicted Educational Domain
                </div>
              </div>
            </div>

            <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div className="stat-icon sky" style={{ background: '#ccfbf1', color: '#0d9488', marginBottom: 0 }}>
                <BookOpen size={24} />
              </div>
              <div>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {(analysisResult.topics?.covered?.length || 0) + (analysisResult.topics?.partially_covered?.length || 0) + (analysisResult.topics?.missing?.length || 0)}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Syllabus Topics Evaluated
                </div>
              </div>
            </div>
          </div>

          {/* Topic Coverage Breakdown (Green, Yellow, Red States) */}
          <div className="dash-card">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1.25rem' }}>
              Syllabus Coverage Breakdown
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
              {/* COVERED (Green) */}
              <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#047857', fontWeight: 700, marginBottom: '0.75rem', fontSize: '0.95rem' }}>
                  <CheckCircle2 size={18} /> Covered Topics ({analysisResult.topics?.covered?.length || 0})
                </div>
                {analysisResult.topics?.covered?.length > 0 ? (
                  <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {analysisResult.topics.covered.map((t, i) => (
                      <li key={i} style={{ fontSize: '0.85rem', color: '#065f46', background: '#ffffff', padding: '0.4rem 0.65rem', borderRadius: '6px', border: '1px solid #d1fae5' }}>
                        {t}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: '#047857', fontStyle: 'italic' }}>No topics fully covered yet.</div>
                )}
              </div>

              {/* PARTIALLY COVERED (Yellow/Amber) */}
              <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#b45309', fontWeight: 700, marginBottom: '0.75rem', fontSize: '0.95rem' }}>
                  <AlertTriangle size={18} /> Partially Covered ({analysisResult.topics?.partially_covered?.length || 0})
                </div>
                {analysisResult.topics?.partially_covered?.length > 0 ? (
                  <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {analysisResult.topics.partially_covered.map((t, i) => (
                      <li key={i} style={{ fontSize: '0.85rem', color: '#92400e', background: '#ffffff', padding: '0.4rem 0.65rem', borderRadius: '6px', border: '1px solid #fef3c7' }}>
                        {t}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: '#b45309', fontStyle: 'italic' }}>No partially covered topics.</div>
                )}
              </div>

              {/* MISSING (Red) */}
              <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#b91c1c', fontWeight: 700, marginBottom: '0.75rem', fontSize: '0.95rem' }}>
                  <XCircle size={18} /> Missing Topics ({analysisResult.topics?.missing?.length || 0})
                </div>
                {analysisResult.topics?.missing?.length > 0 ? (
                  <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {analysisResult.topics.missing.map((t, i) => (
                      <li key={i} style={{ fontSize: '0.85rem', color: '#991b1b', background: '#ffffff', padding: '0.4rem 0.65rem', borderRadius: '6px', border: '1px solid #fee2e2' }}>
                        {t}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: '#b91c1c', fontStyle: 'italic' }}>Great! No missing topics.</div>
                )}
              </div>
            </div>
          </div>

          {/* Recommendations & Actionable Guidance */}
          <div className="dash-card">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Lightbulb size={20} style={{ color: 'var(--primary-accent)' }} /> Personalized Study Recommendations
            </h3>

            {analysisResult.recommendations?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {analysisResult.recommendations.map((rec, i) => (
                  <div 
                    key={i} 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'flex-start', 
                      gap: '1rem', 
                      padding: '1rem', 
                      background: rec.priority === 'HIGH' ? '#fff5f5' : 'var(--bg-card-subtle)', 
                      borderRadius: 'var(--radius-md)',
                      borderLeft: rec.priority === 'HIGH' ? '4px solid #ef4444' : '4px solid #f59e0b'
                    }}
                  >
                    <span 
                      style={{ 
                        padding: '0.2rem 0.5rem', 
                        fontSize: '0.75rem', 
                        fontWeight: 800, 
                        borderRadius: '4px', 
                        background: rec.priority === 'HIGH' ? '#fee2e2' : '#fef3c7',
                        color: rec.priority === 'HIGH' ? '#991b1b' : '#92400e'
                      }}
                    >
                      {rec.priority}
                    </span>
                    <div>
                      <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>{rec.topic}</strong>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{rec.recommendation}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>All syllabus topics are well covered in your study notes!</p>
            )}
          </div>

          {/* Summary & Key Concepts Row */}
          <div className="dashboard-grid" style={{ gridTemplateColumns: '1.4fr 1fr' }}>
            {/* Extractive Summary */}
            <div className="dash-card">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1rem' }}>
                Extractive Notes Summary
              </h3>
              {analysisResult.summary?.length > 0 ? (
                <ul style={{ paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  {analysisResult.summary.map((sent, i) => (
                    <li key={i} style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: '1.5' }}>
                      {sent}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No summary generated.</p>
              )}
            </div>

            {/* Key Concepts Badges */}
            <div className="dash-card">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1rem' }}>
                Extracted Key Concepts
              </h3>
              {analysisResult.key_concepts?.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {analysisResult.key_concepts.map((concept, i) => (
                    <span 
                      key={i} 
                      style={{ 
                        background: 'var(--primary-light)', 
                        color: 'var(--primary-accent)', 
                        padding: '0.4rem 0.75rem', 
                        borderRadius: '9999px', 
                        fontSize: '0.85rem', 
                        fontWeight: 600 
                      }}
                    >
                      {concept}
                    </span>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No key concepts extracted.</p>
              )}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
