import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Upload from './pages/Upload';
import MySyllabus from './pages/MySyllabus';
import AnalyzeNotes from './pages/AnalyzeNotes';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="upload" element={<Upload />} />
          <Route path="syllabus" element={<MySyllabus />} />
          <Route path="analyze" element={<AnalyzeNotes />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="results" element={<Results />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
