import React, { useState } from 'react';
import axios from 'axios';
import { 
  BrainCircuit, FileText, BookOpen, Loader2, UploadCloud, AlertCircle, 
  CheckCircle2, PlusCircle, MinusCircle, Check, Copy, Download, Sparkles,
  Layers, AlertTriangle, ArrowRight, RefreshCw, FileCheck, Zap
} from 'lucide-react';
import { analyzeNotesClientSide } from '../utils/notesAnalyzerClient';

const API_BASE_URL = 'http://localhost:8000/api';

const SAMPLE_SYLLABUS = `Chapter 1: Electric Charges and Fields
- Electric Charge, Conservation and Quantization (q = ne)
- Coulomb's Law and Electrostatic Force (F = k*q1*q2/r^2)
- Electric Field and Superposition Principle
- Electric Field Lines and their Properties
- Electric Dipole and Torque (tau = p*E*sin theta)
- Electric Field Due to Dipole on Axial and Equatorial Lines
- Electric Flux and Gauss's Theorem
- Field Due to Infinitely Long Straight Charged Wire (E = lambda / 2*pi*epsilon0*r)
- Field Due to Uniformly Charged Infinite Plane Sheet (E = sigma / 2*epsilon0)
- Field Due to Uniformly Charged Thin Spherical Shell (E_in = 0, E_out = kQ/r^2)`;

const SAMPLE_NOTES = `Coulomb's Law states that force between two point charges is directly proportional to distance r.
Electric field is defined as force per unit test charge E = F/q with lines extending outward.
Electric dipole moment is p = q*2a, pointing from negative to positive charge.
We also learned about weather patterns, monsoon winds, and rainfall in coastal geography.`;

export default function AnalyzeNotes() {
  const [syllabusFile, setSyllabusFile] = useState(null);
  const [noteFile, setNoteFile] = useState(null);
  const [syllabusText, setSyllabusText] = useState(SAMPLE_SYLLABUS);
  const [noteText, setNoteText] = useState(SAMPLE_NOTES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [engineMode, setEngineMode] = useState('auto'); // 'backend' | 'client'

  // Studio Interactive State
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'missing' | 'extra' | 'correct' | 'editor'
  const [refinedNotes, setRefinedNotes] = useState('');
  const [addedTopicIds, setAddedTopicIds] = useState(new Set());
  const [removedExtraIds, setRemovedExtraIds] = useState(new Set());
  const [appliedCorrectionIds, setAppliedCorrectionIds] = useState(new Set());
  const [copySuccess, setCopySuccess] = useState(false);

  // File text reader helper for client-side mode
  const readFileAsText = (file) => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result || '');
      reader.onerror = () => resolve('');
      reader.readAsText(file);
    });
  };

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');
    setAnalysisResult(null);
    setAddedTopicIds(new Set());
    setRemovedExtraIds(new Set());
    setAppliedCorrectionIds(new Set());

    let finalNoteText = noteText;
    let finalSyllabusText = syllabusText;

    if (noteFile) {
      const readN = await readFileAsText(noteFile);
      if (readN && readN.length > 5 && !readN.startsWith('%PDF')) {
        finalNoteText = readN;
      }
    }
    if (syllabusFile) {
      const readS = await readFileAsText(syllabusFile);
      if (readS && readS.length > 5 && !readS.startsWith('%PDF')) {
        finalSyllabusText = readS;
      }
    }

    // Attempt Backend API if reachable, with instant zero-failure Client-side fallback
    try {
      let responseData = null;
      try {
        if (syllabusFile || noteFile) {
          const formData = new FormData();
          if (syllabusFile) formData.append('syllabus_file', syllabusFile);
          else formData.append('syllabus_text', finalSyllabusText);

          if (noteFile) formData.append('note_file', noteFile);
          else formData.append('note_text', finalNoteText);

          const response = await axios.post(`${API_BASE_URL}/analyze-notes/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 5000
          });
          responseData = response.data;
          setEngineMode('backend');
        } else {
          if (!finalNoteText.trim() || !finalSyllabusText.trim()) {
            setError('Please provide both study notes and syllabus topics (or upload files).');
            setLoading(false);
            return;
          }
          const response = await axios.post(`${API_BASE_URL}/analyze-notes/`, {
            note_text: finalNoteText,
            syllabus_text: finalSyllabusText,
          }, { timeout: 5000 });
          responseData = response.data;
          setEngineMode('backend');
        }
      } catch (backendErr) {
        // Backend not running or unreachable -> Fallback seamlessly to Client-Side Engine!
        console.warn('Backend server not connected. Running Standalone In-Browser NLP Engine...');
        responseData = analyzeNotesClientSide(finalNoteText, finalSyllabusText);
        setEngineMode('client');
      }

      setAnalysisResult(responseData);
      setRefinedNotes(responseData.refined_notes_draft || finalNoteText);
      setActiveTab('overview');
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to analyze notes.');
    } finally {
      setLoading(false);
    }
  };

  // Add a specific missing topic's solution to the notes draft
  const handleAddMissingTopic = (topicObj) => {
    const snippet = topicObj.addable_snippet || `### ${topicObj.topic}\n**Definition:** ${topicObj.definition}\n${topicObj.formulas?.length ? `**Formulas:** ${topicObj.formulas.join(', ')}` : ''}`;
    
    if (!addedTopicIds.has(topicObj.topic)) {
      setRefinedNotes(prev => `${prev.trim()}\n\n---\n${snippet}`);
      setAddedTopicIds(prev => new Set([...prev, topicObj.topic]));
    }
  };

  // Remove a specific extraneous paragraph from the notes draft
  const handleRemoveExtraSection = (extraObj) => {
    if (!removedExtraIds.has(extraObj.id)) {
      setRefinedNotes(prev => {
        const textToRemove = extraObj.text.trim();
        return prev.replace(textToRemove, '').replace(/\n{3,}/g, '\n\n').trim();
      });
      setRemovedExtraIds(prev => new Set([...prev, extraObj.id]));
    }
  };

  // Apply a specific correction to the notes draft
  const handleApplyCorrection = (corrObj) => {
    if (!appliedCorrectionIds.has(corrObj.id)) {
      setRefinedNotes(prev => {
        if (corrObj.original_snippet && corrObj.corrected_version) {
          return prev.replace(corrObj.original_snippet, corrObj.corrected_version);
        }
        return prev;
      });
      setAppliedCorrectionIds(prev => new Set([...prev, corrObj.id]));
    }
  };

  // One-click apply all enhancements
  const handleApplyAll = () => {
    if (analysisResult?.refined_notes_draft) {
      setRefinedNotes(analysisResult.refined_notes_draft);
      if (analysisResult.missing_solutions) {
        setAddedTopicIds(new Set(analysisResult.missing_solutions.map(m => m.topic)));
      }
      if (analysisResult.extra_notes) {
        setRemovedExtraIds(new Set(analysisResult.extra_notes.map(e => e.id)));
      }
      if (analysisResult.corrections) {
        setAppliedCorrectionIds(new Set(analysisResult.corrections.map(c => c.id)));
      }
    }
  };

  // Copy notes to clipboard
  const handleCopyNotes = () => {
    navigator.clipboard.writeText(refinedNotes);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2500);
  };

  // Download Notes as text file
  const handleDownloadNotesFile = () => {
    const element = document.createElement("a");
    const file = new Blob([refinedNotes], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = "Refined_Study_Notes.txt";
    document.body.appendChild(element);
    element.click();
    element.remove();
  };

  // Download PDF Report
  const handleDownloadPDF = async () => {
    if (!analysisResult) return;
    try {
      const response = await axios.post(`${API_BASE_URL}/download-pdf/`, analysisResult, {
        responseType: 'blob',
        timeout: 4000
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'RecoMind_Analysis_Report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      // Fallback: Trigger browser print
      window.print();
    }
  };

  return (
    <div className="analyze-notes-page" style={{ maxWidth: '1080px', margin: '0 auto', paddingBottom: '3rem' }}>
      
      {/* Header */}
      <header className="page-header" style={{ marginBottom: '1.75rem', textAlign: 'center' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: '#ecfdf5', padding: '0.35rem 1rem', borderRadius: '9999px', color: '#047857', fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.5rem', border: '1px solid #a7f3d0' }}>
          <Zap size={16} /> Instant In-Browser NLP Studio (Zero Backend Connection Required)
        </div>
        <h1 className="page-title" style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
          RecoMind Notes Quality & Correction Studio
        </h1>
        <p className="page-subtitle" style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '650px', margin: '0.35rem auto 0 auto' }}>
          Evaluate topic coverage, identify missing concepts with full solutions, remove out-of-syllabus tangents, and check & correct errors.
        </p>
      </header>

      {/* Input Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
        
        {/* STEP 1: Syllabus Upload / Input */}
        <div className="dash-card" style={{ border: '1px solid #cbd5e1', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <label style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BookOpen size={18} style={{ color: 'var(--primary-accent)' }} /> 1. Syllabus (Chapter Topics)
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
              accept=".pdf,.docx,.doc,image/*,.txt" 
              onChange={(e) => { if (e.target.files?.[0]) setSyllabusFile(e.target.files[0]); }} 
              style={{ display: 'none' }} 
            />
            <label htmlFor="syllabusFileInput" style={{ cursor: 'pointer', display: 'block' }}>
              <UploadCloud size={22} style={{ color: 'var(--primary-accent)', margin: '0 auto 0.25rem auto' }} />
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--primary-accent)' }}>
                {syllabusFile ? syllabusFile.name : 'Upload Syllabus Document / Text'}
              </div>
            </label>
          </div>

          <textarea
            rows={5}
            value={syllabusText}
            onChange={(e) => { setSyllabusText(e.target.value); setSyllabusFile(null); }}
            placeholder="Or paste syllabus chapter topics here..."
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #e2e8f0',
              fontFamily: 'inherit',
              fontSize: '0.85rem',
              outline: 'none',
              resize: 'vertical',
              background: '#ffffff'
            }}
          />
        </div>

        {/* STEP 2: Notes Upload / Input */}
        <div className="dash-card" style={{ border: '1px solid #cbd5e1', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <label style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={18} style={{ color: '#047857' }} /> 2. Student Notes (Upload / Paste)
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
              accept=".pdf,.docx,.doc,image/*,.txt" 
              onChange={(e) => { if (e.target.files?.[0]) setNoteFile(e.target.files[0]); }} 
              style={{ display: 'none' }} 
            />
            <label htmlFor="noteFileInput" style={{ cursor: 'pointer', display: 'block' }}>
              <UploadCloud size={22} style={{ color: '#047857', margin: '0 auto 0.25rem auto' }} />
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#047857' }}>
                {noteFile ? noteFile.name : 'Upload Notes Document / Text'}
              </div>
            </label>
          </div>

          <textarea
            rows={5}
            value={noteText}
            onChange={(e) => { setNoteText(e.target.value); setNoteFile(null); }}
            placeholder="Or paste your study notes here..."
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #e2e8f0',
              fontFamily: 'inherit',
              fontSize: '0.85rem',
              outline: 'none',
              resize: 'vertical',
              background: '#ffffff'
            }}
          />
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div style={{ padding: '0.85rem 1.25rem', background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.9rem', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* STEP 3: Analyze Button */}
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="btn-new"
          style={{ padding: '0.9rem 2.75rem', fontSize: '1.05rem', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? (
            <>
              <Loader2 size={20} className="spin" style={{ animation: 'spin 1s linear infinite' }} /> Analyzing & Diagnosing Notes...
            </>
          ) : (
            <>
              <BrainCircuit size={22} /> Analyze Notes & Generate Solutions
            </>
          )}
        </button>
      </div>

      {/* ========================================================================= */}
      {/* STEP 4: INTERACTIVE NOTES STUDIO (RESULTS) */}
      {/* ========================================================================= */}
      {analysisResult && (
        <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
          
          {/* Scorecard Hero Banner */}
          <div 
            className="dash-card"
            style={{
              background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
              borderRadius: 'var(--radius-lg, 20px)',
              padding: '2rem',
              marginBottom: '1.5rem',
              border: '1px solid #e2e8f0',
              boxShadow: '0 10px 30px -5px rgba(0,0,0,0.06)'
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: '2rem', alignItems: 'center' }}>
              
              {/* Coverage Circle */}
              <div style={{ textAlign: 'center', padding: '1rem 1.5rem', background: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.04)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
                  Coverage
                </div>
                <div style={{ fontSize: '3.5rem', fontWeight: 900, lineHeight: 1, color: analysisResult.coverage_percentage >= 75 ? '#047857' : (analysisResult.coverage_percentage >= 45 ? '#b45309' : '#b91c1c') }}>
                  {analysisResult.coverage_percentage}%
                </div>
                <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                  {analysisResult.overall_status}
                </div>
              </div>

              {/* High Level Diagnostic Summary */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <span style={{ background: '#dbeafe', color: '#1e40af', padding: '0.2rem 0.65rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 700 }}>
                    Domain: {analysisResult.domain || 'Education'}
                  </span>
                  <span style={{ background: '#f1f5f9', color: '#475569', padding: '0.2rem 0.65rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 700 }}>
                    Quality: {analysisResult.quality_score || 'Good'}
                  </span>
                  <span style={{ background: '#ecfdf5', color: '#047857', padding: '0.2rem 0.65rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700 }}>
                    ⚡ {engineMode === 'client' ? 'Client Engine' : 'Hybrid AI Engine'}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
                  Academic Assessment Summary
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                  {analysisResult.summary?.[0] || 'Analysis completed successfully.'}
                </p>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <button
                  onClick={handleApplyAll}
                  className="btn-new"
                  style={{ padding: '0.65rem 1.25rem', fontSize: '0.85rem' }}
                >
                  <Sparkles size={16} /> Apply All Enhancements
                </button>
                <button
                  onClick={handleDownloadPDF}
                  style={{ padding: '0.65rem 1.25rem', fontSize: '0.85rem', background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '9999px', fontWeight: 700, color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
                >
                  <Download size={16} /> Export PDF Report
                </button>
              </div>

            </div>

            {/* Quick Metrics Bar */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid #e2e8f0' }}>
              <div style={{ background: '#ecfdf5', padding: '0.75rem', borderRadius: 'var(--radius-sm)', textAlign: 'center', border: '1px solid #a7f3d0' }}>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#047857' }}>{analysisResult.covered_count ?? analysisResult.topics?.covered?.length ?? 0}</div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#065f46' }}>Covered Topics</div>
              </div>
              <div style={{ background: '#fffbeb', padding: '0.75rem', borderRadius: 'var(--radius-sm)', textAlign: 'center', border: '1px solid #fde68a' }}>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#b45309' }}>{analysisResult.partial_count ?? analysisResult.topics?.partially_covered?.length ?? 0}</div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#92400e' }}>Partial Topics</div>
              </div>
              <div style={{ background: '#fef2f2', padding: '0.75rem', borderRadius: 'var(--radius-sm)', textAlign: 'center', border: '1px solid #fecaca' }}>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#b91c1c' }}>{analysisResult.missing_count ?? analysisResult.topics?.missing?.length ?? 0}</div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#991b1b' }}>Missing Topics</div>
              </div>
              <div style={{ background: '#f5f3ff', padding: '0.75rem', borderRadius: 'var(--radius-sm)', textAlign: 'center', border: '1px solid #ddd6fe' }}>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#6d28d9' }}>{analysisResult.extra_notes?.length || 0}</div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#5b21b6' }}>Extra to Remove</div>
              </div>
              <div style={{ background: '#eff6ff', padding: '0.75rem', borderRadius: 'var(--radius-sm)', textAlign: 'center', border: '1px solid #bfdbfe' }}>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#1d4ed8' }}>{analysisResult.corrections?.length || 0}</div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#1e40af' }}>Errors Corrected</div>
              </div>
            </div>

          </div>

          {/* Interactive Navigation Tabs */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => setActiveTab('overview')}
              style={{
                padding: '0.65rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: activeTab === 'overview' ? 'var(--primary-accent)' : 'transparent',
                color: activeTab === 'overview' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <Layers size={16} /> Overview & Topics
            </button>

            <button
              onClick={() => setActiveTab('missing')}
              style={{
                padding: '0.65rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: activeTab === 'missing' ? 'var(--primary-accent)' : 'transparent',
                color: activeTab === 'missing' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <PlusCircle size={16} /> Missing Topic Solutions ({analysisResult.missing_solutions?.length || 0})
            </button>

            <button
              onClick={() => setActiveTab('extra')}
              style={{
                padding: '0.65rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: activeTab === 'extra' ? 'var(--primary-accent)' : 'transparent',
                color: activeTab === 'extra' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <MinusCircle size={16} /> Extra Notes to Remove ({analysisResult.extra_notes?.length || 0})
            </button>

            <button
              onClick={() => setActiveTab('correct')}
              style={{
                padding: '0.65rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: activeTab === 'correct' ? 'var(--primary-accent)' : 'transparent',
                color: activeTab === 'correct' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <CheckCircle2 size={16} /> Check & Correct ({analysisResult.corrections?.length || 0})
            </button>

            <button
              onClick={() => setActiveTab('editor')}
              style={{
                padding: '0.65rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: activeTab === 'editor' ? '#047857' : 'transparent',
                color: activeTab === 'editor' ? '#ffffff' : '#047857',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                marginLeft: 'auto'
              }}
            >
              <FileCheck size={16} /> Master Refined Notes
            </button>
          </div>

          {/* TAB 1: OVERVIEW & TOPICS BREAKDOWN */}
          {activeTab === 'overview' && (
            <div className="dash-card" style={{ padding: '1.75rem' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1rem', color: 'var(--text-primary)' }}>
                Syllabus Topic Breakdown
              </h4>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {analysisResult.topics?.covered?.map((t, idx) => (
                  <div key={idx} style={{ padding: '0.85rem 1.25rem', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#065f46' }}>{t}</span>
                    <span style={{ background: '#047857', color: '#ffffff', padding: '0.2rem 0.65rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 800 }}>COVERED</span>
                  </div>
                ))}

                {analysisResult.topics?.partially_covered?.map((t, idx) => (
                  <div key={idx} style={{ padding: '0.85rem 1.25rem', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#92400e' }}>{t}</span>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <span style={{ background: '#b45309', color: '#ffffff', padding: '0.2rem 0.65rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 800 }}>PARTIAL</span>
                      <button onClick={() => setActiveTab('missing')} style={{ background: 'none', border: 'none', color: '#b45309', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer', textDecoration: 'underline' }}>View Solution →</button>
                    </div>
                  </div>
                ))}

                {analysisResult.topics?.missing?.map((t, idx) => (
                  <div key={idx} style={{ padding: '0.85rem 1.25rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#991b1b' }}>{t}</span>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <span style={{ background: '#b91c1c', color: '#ffffff', padding: '0.2rem 0.65rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 800 }}>MISSING</span>
                      <button onClick={() => setActiveTab('missing')} style={{ background: 'none', border: 'none', color: '#b91c1c', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer', textDecoration: 'underline' }}>View Solution →</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: MISSING TOPIC SOLUTIONS */}
          {activeTab === 'missing' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {analysisResult.missing_solutions && analysisResult.missing_solutions.length > 0 ? (
                analysisResult.missing_solutions.map((sol, idx) => {
                  const isAdded = addedTopicIds.has(sol.topic);
                  return (
                    <div key={idx} className="dash-card" style={{ padding: '1.75rem', border: '1px solid #cbd5e1', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
                            <span style={{ background: sol.status === 'MISSING' ? '#fef2f2' : '#fffbeb', color: sol.status === 'MISSING' ? '#b91c1c' : '#b45309', border: `1px solid ${sol.status === 'MISSING' ? '#fecaca' : '#fde68a'}`, padding: '0.15rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 800 }}>
                              {sol.status}
                            </span>
                            <h4 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                              {sol.topic}
                            </h4>
                          </div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            Missing: {sol.missing_aspects?.join(', ')}
                          </div>
                        </div>

                        <button
                          onClick={() => handleAddMissingTopic(sol)}
                          style={{
                            padding: '0.55rem 1.1rem',
                            borderRadius: '9999px',
                            border: isAdded ? '1px solid #a7f3d0' : 'none',
                            background: isAdded ? '#ecfdf5' : 'var(--primary-accent)',
                            color: isAdded ? '#047857' : '#ffffff',
                            fontWeight: 700,
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                            transition: 'all 0.2s'
                          }}
                        >
                          {isAdded ? <><Check size={16} /> Added to Notes</> : <><PlusCircle size={16} /> Add to Notes Draft</>}
                        </button>
                      </div>

                      {/* Content Card Body */}
                      <div style={{ background: 'var(--bg-card-subtle)', padding: '1.25rem', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
                        {sol.definition && (
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Definition: </strong>
                            <span style={{ color: 'var(--text-secondary)' }}>{sol.definition}</span>
                          </div>
                        )}

                        {sol.formulas && sol.formulas.length > 0 && (
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Formulas: </strong>
                            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.35rem', flexWrap: 'wrap' }}>
                              {sol.formulas.map((f, fIdx) => (
                                <code key={fIdx} style={{ background: '#ffffff', border: '1px solid #cbd5e1', padding: '0.25rem 0.65rem', borderRadius: '6px', fontSize: '0.85rem', color: '#1e293b' }}>
                                  {f}
                                </code>
                              ))}
                            </div>
                          </div>
                        )}

                        {sol.derivation && sol.derivation.length > 0 && (
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Step-by-Step Derivation / Concept: </strong>
                            <ul style={{ paddingLeft: '1.25rem', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>
                              {sol.derivation.map((d, dIdx) => (
                                <li key={dIdx}>{d}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {sol.important_points && sol.important_points.length > 0 && (
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Key Retention Points: </strong>
                            <ul style={{ paddingLeft: '1.25rem', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>
                              {sol.important_points.map((pt, pIdx) => (
                                <li key={pIdx}>{pt}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {sol.example && (
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Worked Example: </strong>
                            <span style={{ color: 'var(--text-secondary)' }}>{sol.example}</span>
                          </div>
                        )}

                        {sol.exam_tip && (
                          <div style={{ padding: '0.65rem 0.85rem', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '6px', color: '#1e40af', fontSize: '0.85rem' }}>
                            💡 <strong>Exam Tip:</strong> {sol.exam_tip}
                          </div>
                        )}
                      </div>

                    </div>
                  );
                })
              ) : (
                <div className="dash-card" style={{ textAlign: 'center', padding: '3rem 1.5rem', color: '#047857' }}>
                  <CheckCircle2 size={36} style={{ margin: '0 auto 0.75rem auto' }} />
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>No Missing Topics Found!</h3>
                  <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Your notes cover all topics required by this syllabus chapter.</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: EXTRA NOTES (TO REMOVE) */}
          {activeTab === 'extra' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {analysisResult.extra_notes && analysisResult.extra_notes.length > 0 ? (
                analysisResult.extra_notes.map((extra, idx) => {
                  const isRemoved = removedExtraIds.has(extra.id);
                  return (
                    <div key={idx} className="dash-card" style={{ padding: '1.75rem', border: '1px solid #fde68a', background: isRemoved ? '#f8fafc' : '#fffdf5' }}>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                            <AlertTriangle size={18} style={{ color: '#b45309' }} />
                            <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#92400e' }}>
                              Out-of-Syllabus / Extraneous Section
                            </h4>
                          </div>
                          <p style={{ fontSize: '0.85rem', color: '#b45309', marginTop: '0.25rem' }}>
                            {extra.reason}
                          </p>
                        </div>

                        <button
                          onClick={() => handleRemoveExtraSection(extra)}
                          style={{
                            padding: '0.55rem 1.1rem',
                            borderRadius: '9999px',
                            border: isRemoved ? '1px solid #cbd5e1' : '1px solid #fca5a5',
                            background: isRemoved ? '#f1f5f9' : '#fef2f2',
                            color: isRemoved ? '#64748b' : '#b91c1c',
                            fontWeight: 700,
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.4rem'
                          }}
                        >
                          {isRemoved ? <><Check size={16} /> Removed from Draft</> : <><MinusCircle size={16} /> Remove from Notes</>}
                        </button>
                      </div>

                      <div style={{ padding: '1rem', background: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid #fde68a', fontSize: '0.9rem', color: isRemoved ? '#94a3b8' : 'var(--text-primary)', textDecoration: isRemoved ? 'line-through' : 'none' }}>
                        "{extra.text}"
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="dash-card" style={{ textAlign: 'center', padding: '3rem 1.5rem', color: '#047857' }}>
                  <CheckCircle2 size={36} style={{ margin: '0 auto 0.75rem auto' }} />
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>No Out-of-Syllabus Notes Detected</h3>
                  <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>All content in your uploaded notes is relevant to the syllabus.</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: CHECK & CORRECT */}
          {activeTab === 'correct' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {analysisResult.corrections && analysisResult.corrections.length > 0 ? (
                analysisResult.corrections.map((corr, idx) => {
                  const isCorrected = appliedCorrectionIds.has(corr.id);
                  return (
                    <div key={idx} className="dash-card" style={{ padding: '1.75rem', border: '1px solid #cbd5e1' }}>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                        <div>
                          <span style={{ background: '#eff6ff', color: '#1d4ed8', padding: '0.15rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 800 }}>
                            {corr.topic}
                          </span>
                          <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.35rem' }}>
                            {corr.issue}
                          </h4>
                        </div>

                        <button
                          onClick={() => handleApplyCorrection(corr)}
                          style={{
                            padding: '0.55rem 1.1rem',
                            borderRadius: '9999px',
                            border: isCorrected ? '1px solid #a7f3d0' : 'none',
                            background: isCorrected ? '#ecfdf5' : '#047857',
                            color: isCorrected ? '#047857' : '#ffffff',
                            fontWeight: 700,
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.4rem'
                          }}
                        >
                          {isCorrected ? <><Check size={16} /> Correction Applied</> : <><CheckCircle2 size={16} /> Apply Correction</>}
                        </button>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.75rem' }}>
                        
                        {/* Original with Error */}
                        <div style={{ padding: '1rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-md)' }}>
                          <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#b91c1c', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                            ❌ In Your Notes:
                          </div>
                          <div style={{ fontSize: '0.9rem', color: '#991b1b' }}>
                            "{corr.original_snippet}"
                          </div>
                        </div>

                        {/* Verified Correction */}
                        <div style={{ padding: '1rem', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 'var(--radius-md)' }}>
                          <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#047857', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                            ✨ Corrected Academic Formulation:
                          </div>
                          <div style={{ fontSize: '0.9rem', color: '#065f46' }}>
                            "{corr.corrected_version}"
                          </div>
                        </div>

                      </div>

                    </div>
                  );
                })
              ) : (
                <div className="dash-card" style={{ textAlign: 'center', padding: '3rem 1.5rem', color: '#047857' }}>
                  <CheckCircle2 size={36} style={{ margin: '0 auto 0.75rem auto' }} />
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>No Conceptual Mistakes Found</h3>
                  <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>The formulations and principles in your notes are scientifically accurate.</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: MASTER REFINED NOTES EDITOR */}
          {activeTab === 'editor' && (
            <div className="dash-card" style={{ padding: '1.75rem' }}>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div>
                  <h4 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    Master Refined Notes
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Includes verified notes, applied error corrections, extra content stripped, and added missing topics.
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button
                    onClick={handleCopyNotes}
                    style={{ padding: '0.55rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid #cbd5e1', background: '#ffffff', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                  >
                    {copySuccess ? <><Check size={16} style={{ color: '#047857' }} /> Copied!</> : <><Copy size={16} /> Copy Notes</>}
                  </button>

                  <button
                    onClick={handleDownloadNotesFile}
                    style={{ padding: '0.55rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid #cbd5e1', background: '#ffffff', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                  >
                    <Download size={16} /> Download .txt
                  </button>

                  <button
                    onClick={handleDownloadPDF}
                    className="btn-new"
                    style={{ padding: '0.55rem 1.25rem', fontSize: '0.85rem' }}
                  >
                    <Download size={16} /> Export PDF Report
                  </button>
                </div>
              </div>

              <textarea
                rows={16}
                value={refinedNotes}
                onChange={(e) => setRefinedNotes(e.target.value)}
                style={{
                  width: '100%',
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #cbd5e1',
                  fontFamily: 'ui-monospace, monospace',
                  fontSize: '0.9rem',
                  lineHeight: 1.6,
                  outline: 'none',
                  resize: 'vertical',
                  background: '#f8fafc',
                  color: '#1e293b'
                }}
              />

            </div>
          )}

        </div>
      )}

    </div>
  );
}
