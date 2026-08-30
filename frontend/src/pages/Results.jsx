import React from 'react';
import { FileText, Download, Share2 } from 'lucide-react';

const placeholderNotes = [
  { id: 1, title: 'Linear Algebra Lecture 4 Notes', date: '2026-08-18', score: '92/100', status: 'Completed' },
  { id: 2, title: 'Organic Chemistry Formulas', date: '2026-08-17', score: '85/100', status: 'Completed' },
  { id: 3, title: 'Data Structures Tree Traversal', date: '2026-08-15', score: '88/100', status: 'Completed' },
];

export default function Results() {
  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>My Results</h1>
        <p style={{ color: 'var(--text-secondary)' }}>View evaluated notes and extracted details.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {placeholderNotes.map((note) => (
          <div key={note.id} className="dash-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div className="stat-icon blue" style={{ marginBottom: 0 }}>
                <FileText size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>{note.title}</h3>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
                  Uploaded on {note.date} • <span style={{ color: 'var(--primary-accent)', fontWeight: 600 }}>Score: {note.score}</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="icon-btn" title="Share Note">
                <Share2 size={16} />
              </button>
              <button className="btn-new" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                <Download size={14} /> Export Report
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
