import React from 'react';
import { X, AlertCircle } from 'lucide-react';

export default function AnalysisReportModal({ isOpen, onClose, data }) {
  if (!isOpen || !data) return null;

  const coveragePct = data.coverage_percentage || 0;
  const weakTopics = data.weak_topics || data.missing_topics || [];

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
          borderRadius: 'var(--radius-lg, 16px)',
          width: '100%',
          maxWidth: '520px',
          display: 'flex',
          flexDirection: 'column',
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
          <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            RecoMind Analysis Result
          </div>
          <button 
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '0.5rem' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '2rem 1.75rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* NOTES COVERAGE */}
          <div style={{ textAlign: 'center', paddingBottom: '1.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 800, letterSpacing: '0.08em', color: 'var(--text-secondary, #64748b)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              NOTES COVERAGE
            </div>
            <div style={{ fontSize: '4rem', fontWeight: 900, lineHeight: 1, color: 'var(--primary-accent, #4361ee)' }}>
              {coveragePct}%
            </div>
          </div>

          {/* WEAK / MISSING TOPICS */}
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 800, letterSpacing: '0.05em', color: '#b91c1c', textTransform: 'uppercase', marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertCircle size={16} /> WEAK / MISSING TOPICS
            </div>

            {weakTopics.length > 0 ? (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {weakTopics.map((topic, idx) => (
                  <li 
                    key={idx} 
                    style={{ 
                      fontSize: '0.9rem', 
                      fontWeight: 600, 
                      color: 'var(--text-primary)', 
                      background: '#fef2f2', 
                      border: '1px solid #fecaca', 
                      padding: '0.55rem 0.85rem', 
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
              <div style={{ padding: '0.75rem 1rem', background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#047857', borderRadius: 'var(--radius-md)', fontWeight: 700, fontSize: '0.85rem', textAlign: 'center' }}>
                ✨ Excellent! All syllabus topics are well covered.
              </div>
            )}
          </div>

        </div>

        {/* Modal Footer */}
        <div 
          style={{
            padding: '1rem 1.75rem',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            justify: 'flex-end',
            background: 'var(--bg-card-subtle)'
          }}
        >
          <button
            onClick={onClose}
            className="btn-new"
            style={{ padding: '0.55rem 1.5rem', fontSize: '0.85rem' }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

