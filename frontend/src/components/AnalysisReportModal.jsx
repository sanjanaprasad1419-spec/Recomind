import React from 'react';
import { useNavigate } from 'react-router-dom';
import { X, AlertCircle, CheckCircle2, PlusCircle, MinusCircle, Sparkles, Download, ArrowRight } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export default function AnalysisReportModal({ isOpen, onClose, data }) {
  const navigate = useNavigate();
  if (!isOpen || !data) return null;

  const coveragePct = data.coverage_percentage || 0;
  const accuracyScore = data.accuracy_score || coveragePct;
  const qualityRating = data.quality_score || 'Good';
  const missingCount = data.missing_solutions?.length || data.missing_topics?.length || data.weak_topics?.length || 0;
  const extraCount = data.extra_notes?.length || 0;
  const correctionsCount = data.corrections?.length || 0;

  const handleDownloadPDF = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/download-pdf/`, data, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'RecoMind_Analysis_Report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('PDF download error:', err);
    }
  };

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(5px)',
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
          borderRadius: 'var(--radius-lg, 20px)',
          width: '100%',
          maxWidth: '580px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.3)',
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
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'var(--bg-card-subtle)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={18} style={{ color: 'var(--primary-accent)' }} />
            <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              RecoMind Analysis Results
            </span>
          </div>
          <button 
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '0.4rem' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body (Scrollable) */}
        <div style={{ padding: '1.75rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Top Score Banner */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', textAlign: 'center' }}>
            <div style={{ padding: '1.25rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                Coverage
              </div>
              <div style={{ fontSize: '2.75rem', fontWeight: 900, lineHeight: 1, color: coveragePct >= 70 ? '#047857' : (coveragePct >= 45 ? '#b45309' : '#b91c1c') }}>
                {coveragePct}%
              </div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                {data.overall_status || 'Complete'}
              </div>
            </div>

            <div style={{ padding: '1.25rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                Accuracy Rating
              </div>
              <div style={{ fontSize: '2.75rem', fontWeight: 900, lineHeight: 1, color: 'var(--primary-accent)' }}>
                {accuracyScore}%
              </div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                {qualityRating}
              </div>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
            <div style={{ background: '#fef2f2', padding: '0.65rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #fecaca' }}>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#b91c1c' }}>{missingCount}</div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#991b1b' }}>Missing Solutions</div>
            </div>
            <div style={{ background: '#fffbeb', padding: '0.65rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #fde68a' }}>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#b45309' }}>{extraCount}</div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#92400e' }}>Extra to Remove</div>
            </div>
            <div style={{ background: '#ecfdf5', padding: '0.65rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #a7f3d0' }}>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#047857' }}>{correctionsCount}</div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#065f46' }}>Errors Corrected</div>
            </div>
          </div>

          {/* Missing Topics Preview */}
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#b91c1c', textTransform: 'uppercase', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <AlertCircle size={16} /> Missing & Partial Topics
            </div>
            {data.missing_solutions && data.missing_solutions.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {data.missing_solutions.slice(0, 3).map((sol, idx) => (
                  <div key={idx} style={{ padding: '0.65rem 0.85rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', fontSize: '0.85rem' }}>
                    <strong style={{ color: '#991b1b' }}>• {sol.topic}</strong>: <span style={{ color: '#475569' }}>{sol.definition?.slice(0, 85)}...</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '0.65rem', background: '#ecfdf5', borderRadius: '6px', color: '#047857', fontSize: '0.85rem', fontWeight: 700, textAlign: 'center' }}>
                ✨ All syllabus topics are well covered!
              </div>
            )}
          </div>

          {/* Extra Notes to Remove Preview */}
          {data.extra_notes && data.extra_notes.length > 0 && (
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#b45309', textTransform: 'uppercase', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <MinusCircle size={16} /> Extra Out-of-Syllabus Notes
              </div>
              <div style={{ padding: '0.65rem 0.85rem', background: '#fffdf5', border: '1px solid #fde68a', borderRadius: '6px', fontSize: '0.85rem', color: '#92400e' }}>
                Found {data.extra_notes.length} off-topic section(s) ready to be excluded.
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div 
          style={{
            padding: '1rem 1.75rem',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'var(--bg-card-subtle)'
          }}
        >
          <button
            onClick={handleDownloadPDF}
            style={{ padding: '0.55rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid #cbd5e1', background: '#ffffff', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <Download size={15} /> Export PDF
          </button>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={onClose}
              style={{ padding: '0.55rem 1.25rem', borderRadius: 'var(--radius-sm)', border: '1px solid #cbd5e1', background: '#ffffff', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}
            >
              Close
            </button>
            <button
              onClick={() => { onClose(); navigate('/analyze'); }}
              className="btn-new"
              style={{ padding: '0.55rem 1.4rem', fontSize: '0.85rem' }}
            >
              Open in Studio <ArrowRight size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
