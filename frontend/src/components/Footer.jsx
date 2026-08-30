import React from 'react';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <p className="footer-text">
          &copy; {new Date().getFullYear()} RecoMind. AI Notes Quality Analyzer workspace.
        </p>
        <ul className="footer-links">
          <li><a href="#privacy" className="footer-link">Privacy Policy</a></li>
          <li><a href="#terms" className="footer-link">Terms of Service</a></li>
          <li><a href="#docs" className="footer-link">API Docs</a></li>
        </ul>
      </div>
    </footer>
  );
}
