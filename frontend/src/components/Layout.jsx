import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Header from './Header';

export default function Layout() {
  return (
    <div className="app-frame">
      <Navbar />
      <main className="main-viewport">
        <Header />
        <Outlet />
      </main>
    </div>
  );
}
