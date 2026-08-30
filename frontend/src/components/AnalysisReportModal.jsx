import React, { useState } from 'react';
import axios from 'axios';
import { 
  X, Download, CheckCircle2, AlertTriangle, XCircle, 
  BrainCircuit, Sparkles, BookOpen, Lightbulb, FileText, RefreshCw, Loader2, Copy, Check, ChevronRight 
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

export default function AnalysisReportModal({ isOpen, onClose, data }) {
  const [activeTab, setActiveTab] = useState('missing'); // 'missing' or 'enhance'
  const [downloading, setDownloading] = useState(false);
  const [copiedDraft, setCopiedDraft] = useState(false);
  const [copiedParagraphIdx, setCopiedParagraphIdx] = useState(null);

  if (!isOpen || !data) return null;

  const coveragePct = data.coverage_percentage || 0;
  const syllabusTitle = data.syllabus_title || 'General Syllabus';
  const sectionTitle = data.section_title || 'Selected Chapter/Module';
  const topics = data.topics || {};

  const enhancementsList = data.ai_enhancement?.enhancements || data.recommendations || [];

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/analysis/download-pdf/`, data, {
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `RecoMind_${sectionTitle.replace(/[^a-zA-Z0-9]/g, '_')}_Analysis.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF Download Error:', err);
      alert('Failed to download PDF summary report. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyDraft = () => {
    const draftText = data.ai_enhancement?.improved_notes_draft || data.refined_notes_draft;
    if (draftText) {
      navigator.clipboard.writeText(draftText);
      setCopiedDraft(true);
      setTimeout(() => setCopiedDraft(false), 2000);
    }
  };

  const handleCopyParagraph = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedParagraphIdx(idx);
    setTimeout(() => setCopiedParagraphIdx(null), 2000);
  };

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
          maxWidth: '860px',
          maxHeight: '92vh',
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
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--primary-accent)', letterSpacing: '0.05em' }}>
              RECOMMIND ANALYSIS & AI ENHANCEMENT
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>
              {syllabusTitle}
            </h2>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Section: <strong>{sectionTitle}</strong>
            </div>
          </div>
          <button 
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '0.5rem' }}
          >
            <X size={22} />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', background: '#f8fafc' }}>
          <button
            onClick={() => setActiveTab('missing')}
            style={{
              flex: 1,
              padding: '0.85rem',
              fontWeight: 800,
              fontSize: '0.9rem',
              border: 'none',
              borderBottom: activeTab === 'missing' ? '3px solid var(--primary-accent)' : 'none',
              background: activeTab === 'missing' ? '#ffffff' : 'transparent',
              color: activeTab === 'missing' ? 'var(--primary-accent)' : 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justify: 'center',
              gap: '0.5rem'
            }}
          >
            <BrainCircuit size={18} /> A) What am I missing? (ML Analysis)
          </button>

          <button
            onClick={() => setActiveTab('enhance')}
            style={{
              flex: 1,
              padding: '0.85rem',
              fontWeight: 800,
              fontSize: '0.9rem',
              border: 'none',
              borderBottom: activeTab === 'enhance' ? '3px solid #8b5cf6' : 'none',
              background: activeTab === 'enhance' ? '#ffffff' : 'transparent',
              color: activeTab === 'enhance' ? '#8b5cf6' : 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justify: 'center',
              gap: '0.5rem'
            }}
          >
            <Sparkles size={18} /> B) Enhance My Notes (AI Content Generator)
          </button>
        </div>

        {/* Modal Body (Scrollable) */}
        <div style={{ padding: '1.75rem', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* TAB A: WHAT AM I MISSING? */}
          {activeTab === 'missing' && (
            <>
              {/* Coverage Percentage Stat Header */}
              <div 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justify: 'space-between', 
                  background: '#f8fafc', 
                  padding: '1.25rem 1.5rem', 
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)'
                }}
              >
                <div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>ML Topic Coverage Score</div>
                  <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--primary-accent)' }}>
                    {coveragePct}%
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ display: 'inline-block', padding: '0.35rem 0.85rem', borderRadius: '9999px', background: 'var(--primary-light)', color: 'var(--primary-accent)', fontSize: '0.85rem', fontWeight: 700 }}>
                    {data.domain || 'General Education'}
                  </span>
                </div>
              </div>

              {/* COVERED */}
              <div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#047857', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <CheckCircle2 size={18} /> ✅ WELL COVERED ({topics.covered?.length || 0})
                </h3>
                {topics.covered?.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {topics.covered.map((t, idx) => (
                      <span key={idx} style={{ background: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0', padding: '0.4rem 0.75rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600 }}>
                        {t}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>No topics fully covered yet.</div>
                )}
              </div>

              {/* NEEDS IMPROVEMENT */}
              <div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#b45309', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <AlertTriangle size={18} /> ⚠️ NEEDS IMPROVEMENT ({topics.partially_covered?.length || 0})
                </h3>
                {topics.partially_covered?.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {topics.partially_covered.map((t, idx) => (
                      <span key={idx} style={{ background: '#fffbeb', color: '#b45309', border: '1px solid #fde68a', padding: '0.4rem 0.75rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600 }}>
                        {t}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>No topics in partial coverage state.</div>
                )}
              </div>

              {/* MISSING */}
              <div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#b91c1c', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <XCircle size={18} /> ❌ MISSING ({topics.missing?.length || 0})
                </h3>
                {topics.missing?.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {topics.missing.map((t, idx) => (
                      <span key={idx} style={{ background: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca', padding: '0.4rem 0.75rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600 }}>
                        {t}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>Great! No missing topics detected.</div>
                )}
              </div>

              {/* CTA to Tab B */}
              <button
                onClick={() => setActiveTab('enhance')}
                className="btn-new"
                style={{ width: '100%', padding: '0.85rem', justifyContent: 'center', fontSize: '0.95rem', background: '#8b5cf6', color: '#ffffff' }}
              >
                <Sparkles size={18} /> Enhance Notes & Generate Educational Study Cards
              </button>
            </>
          )}

          {/* TAB B: ENHANCE MY NOTES & EDUCATIONAL CARDS */}
          {activeTab === 'enhance' && (
            <>
              {/* Detailed 9-Section Educational Cards for Missing/Weak Topics */}
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <BookOpen size={18} style={{ color: '#8b5cf6' }} /> 📚 AI STUDY MATERIAL GENERATED FOR EACH WEAK/MISSING TOPIC
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {enhancementsList.map((item, idx) => {
                    const tName = item.topic || rec.topic || 'Syllabus Topic';
                    const status = item.status || 'MISSING';
                    const enh = item.enhancement || item;

                    return (
                      <div 
                        key={idx}
                        style={{
                          background: '#ffffff',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-lg)',
                          padding: '1.25rem',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
                          <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>Topic: {tName}</strong>
                          <span style={{ fontSize: '0.75rem', fontWeight: 800, padding: '0.25rem 0.65rem', borderRadius: '4px', background: status === 'MISSING' ? '#fee2e2' : status === 'PARTIALLY_COVERED' ? '#fef3c7' : '#ecfdf5', color: status === 'MISSING' ? '#b91c1c' : status === 'PARTIALLY_COVERED' ? '#b45309' : '#047857' }}>
                            {status === 'MISSING' ? '❌ MISSING' : status === 'PARTIALLY_COVERED' ? '⚠️ PARTIALLY COVERED' : '✅ COVERED'}
                          </span>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                          
                          {/* 1. Definition */}
                          {enh.definition && (
                            <div>
                              <strong style={{ fontSize: '0.8rem', color: 'var(--primary-accent)', display: 'block' }}>📌 Definition:</strong>
                              <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', margin: '2px 0 0 0', lineHeight: '1.5' }}>{enh.definition}</p>
                            </div>
                          )}

                          {/* 2. Concept */}
                          {enh.concept && (
                            <div>
                              <strong style={{ fontSize: '0.8rem', color: '#8b5cf6', display: 'block' }}>💡 Core Concept:</strong>
                              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '2px 0 0 0', lineHeight: '1.5' }}>{enh.concept}</p>
                            </div>
                          )}

                          {/* 3. Formulas */}
                          {enh.formulas && enh.formulas.length > 0 && (
                            <div>
                              <strong style={{ fontSize: '0.8rem', color: '#047857', display: 'block' }}>📐 Key Formula(s):</strong>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', marginTop: '3px' }}>
                                {enh.formulas.map((f, fIdx) => (
                                  <code key={fIdx} style={{ background: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0', padding: '0.4rem 0.65rem', borderRadius: '4px', fontSize: '0.85rem', fontFamily: 'monospace', fontWeight: 700 }}>
                                    {f}
                                  </code>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* 4. Derivation */}
                          {enh.derivation && enh.derivation.length > 0 && (
                            <div>
                              <strong style={{ fontSize: '0.8rem', color: '#1e40af', display: 'block' }}>📝 Derivation Steps:</strong>
                              <ol style={{ paddingLeft: '1.1rem', margin: '3px 0 0 0', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                {enh.derivation.map((step, sIdx) => (
                                  <li key={sIdx} style={{ fontSize: '0.82rem', color: 'var(--text-primary)', lineHeight: '1.4' }}>
                                    {step}
                                  </li>
                                ))}
                              </ol>
                            </div>
                          )}

                          {/* 5. Important Points */}
                          {enh.important_points && enh.important_points.length > 0 && (
                            <div>
                              <strong style={{ fontSize: '0.8rem', color: '#b45309', display: 'block' }}>🔹 Important Points:</strong>
                              <ul style={{ paddingLeft: '1.1rem', margin: '3px 0 0 0', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                {enh.important_points.map((pt, pIdx) => (
                                  <li key={pIdx} style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                                    {pt}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* 6. Example */}
                          {enh.example && (
                            <div>
                              <strong style={{ fontSize: '0.8rem', color: '#6b21a8', display: 'block' }}>🎯 Worked Example:</strong>
                              <p style={{ fontSize: '0.82rem', color: 'var(--text-primary)', background: '#faf5ff', border: '1px solid #e9d5ff', padding: '0.5rem 0.75rem', borderRadius: '6px', margin: '2px 0 0 0' }}>
                                {enh.example}
                              </p>
                            </div>
                          )}

                          {/* 7. Diagram Guidance */}
                          {enh.diagram_guidance && (
                            <div>
                              <strong style={{ fontSize: '0.8rem', color: '#4361ee', display: 'block' }}>🖼️ Diagram Guidance:</strong>
                              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', background: '#eff6ff', border: '1px solid #bfdbfe', padding: '0.5rem 0.75rem', borderRadius: '6px', margin: '2px 0 0 0' }}>
                                {enh.diagram_guidance}
                              </p>
                            </div>
                          )}

                          {/* 8. Exam Tip */}
                          {enh.exam_tip && (
                            <div>
                              <strong style={{ fontSize: '0.8rem', color: '#b91c1c', display: 'block' }}>⚡ Exam / Revision Tip:</strong>
                              <p style={{ fontSize: '0.82rem', color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', padding: '0.5rem 0.75rem', borderRadius: '6px', margin: '2px 0 0 0', fontWeight: 600 }}>
                                {enh.exam_tip}
                              </p>
                            </div>
                          )}

                          {/* 9. Quick Revision */}
                          {enh.quick_revision && (
                            <div style={{ paddingTop: '0.4rem', borderTop: '1px dashed var(--border-subtle)' }}>
                              <strong style={{ fontSize: '0.8rem', color: '#047857' }}>🔄 Quick Revision: </strong>
                              <span style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 600 }}>{enh.quick_revision}</span>
                            </div>
                          )}

                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Improved Notes Draft Card */}
              {(data.ai_enhancement?.improved_notes_draft || data.refined_notes_draft) && (
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Sparkles size={18} style={{ color: 'var(--primary-accent)' }} /> 📝 COMPLETE IMPROVED NOTES DRAFT
                    </h3>
                    <button
                      onClick={handleCopyDraft}
                      className="btn-new"
                      style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', background: copiedDraft ? '#ecfdf5' : 'var(--primary-accent)', color: copiedDraft ? '#047857' : '#ffffff', border: copiedDraft ? '1px solid #a7f3d0' : 'none' }}
                    >
                      {copiedDraft ? <><Check size={14} /> Copied Notes</> : <><Copy size={14} /> Copy Improved Notes</>}
                    </button>
                  </div>

                  <pre 
                    style={{ 
                      background: '#0f172a', 
                      color: '#f8fafc', 
                      padding: '1.25rem', 
                      borderRadius: 'var(--radius-md)', 
                      fontSize: '0.85rem', 
                      lineHeight: '1.6', 
                      whiteSpace: 'pre-wrap', 
                      fontFamily: 'monospace', 
                      maxHeight: '280px', 
                      overflowY: 'auto' 
                    }}
                  >
                    {data.ai_enhancement?.improved_notes_draft || data.refined_notes_draft}
                  </pre>
                </div>
              )}
            </>
          )}

        </div>

        {/* Modal Footer Actions */}
        <div 
          style={{
            padding: '1rem 1.75rem',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            justify: 'space-between',
            alignItems: 'center',
            background: 'var(--bg-card-subtle)'
          }}
        >
          <button
            onClick={handleDownloadPDF}
            disabled={downloading}
            className="btn-new"
            style={{ padding: '0.65rem 1.4rem', fontSize: '0.85rem', cursor: downloading ? 'not-allowed' : 'pointer' }}
          >
            {downloading ? (
              <>
                <Loader2 size={16} className="spin" style={{ animation: 'spin 1s linear infinite' }} /> Generating PDF...
              </>
            ) : (
              <>
                <Download size={16} /> Download Summary (PDF)
              </>
            )}
          </button>

          <button
            onClick={onClose}
            style={{
              padding: '0.65rem 1.4rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              background: '#ffffff',
              color: 'var(--text-primary)',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
