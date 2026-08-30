import React from 'react';
import { NavLink } from 'react-router-dom';
import { Sparkles, LayoutDashboard, UploadCloud, BookOpen, BrainCircuit, FileText, BarChart2, Settings } from 'lucide-react';

export default function Navbar() {
  return (
    <aside className="sidebar">
      <NavLink to="/" className="sidebar-brand">
        <div className="sidebar-brand-icon">
          <Sparkles size={20} />
        </div>
        <span>RecoMind</span>
      </NavLink>

      <ul className="sidebar-menu">
        <li>
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'sidebar-link active' : 'sidebar-link'}>
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </NavLink>
        </li>
        <li>
          <NavLink to="/syllabus" className={({ isActive }) => isActive ? 'sidebar-link active' : 'sidebar-link'}>
            <BookOpen size={18} />
            <span>My Syllabus</span>
          </NavLink>
        </li>
        <li>
          <NavLink to="/upload" className={({ isActive }) => isActive ? 'sidebar-link active' : 'sidebar-link'}>
            <UploadCloud size={18} />
            <span>Upload Notes</span>
          </NavLink>
        </li>
        <li>
          <NavLink to="/analyze" className={({ isActive }) => isActive ? 'sidebar-link active' : 'sidebar-link'}>
            <BrainCircuit size={18} />
            <span>Analyze Notes</span>
          </NavLink>
        </li>
        <li>
          <NavLink to="/results" className={({ isActive }) => isActive ? 'sidebar-link active' : 'sidebar-link'}>
            <FileText size={18} />
            <span>My Results</span>
          </NavLink>
        </li>
      </ul>
    </aside>
  );
}
