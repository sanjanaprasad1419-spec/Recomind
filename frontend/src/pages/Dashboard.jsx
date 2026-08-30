import React from 'react';
import { 
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, 
  XAxis, YAxis, Tooltip, ResponsiveContainer 
} from 'recharts';
import { FileText, Award, Clock, CheckCircle } from 'lucide-react';

const lineData = [
  { name: 'Jan', val: 20 },
  { name: 'Feb', val: 45 },
  { name: 'Mar', val: 30 },
  { name: 'Apr', val: 70 },
  { name: 'May', val: 50 },
  { name: 'Jun', val: 90 },
  { name: 'Jul', val: 65 },
  { name: 'Aug', val: 85 },
];

const barData = [
  { name: 'Jan', a: 200, b: 400 },
  { name: 'Feb', a: 300, b: 500 },
  { name: 'Mar', a: 250, b: 350 },
  { name: 'Apr', a: 400, b: 580 },
  { name: 'May', a: 320, b: 450 },
];

const pieData = [
  { name: 'High Quality', value: 55, color: '#b8c0ff' },
  { name: 'Medium Quality', value: 30, color: '#c8b6ff' },
  { name: 'Low Quality', value: 15, color: '#e7c6ff' },
];

export default function Dashboard() {
  return (
    <div className="dashboard-content">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>My Dashboard</h1>
      </div>

      {/* Top 3 Visual Charts Row matching Screenshot */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
        {/* Line / Smooth Area Chart */}
        <div className="dash-card">
          <div className="dash-card-header">
            <span className="dash-card-title">Line Chart</span>
          </div>
          <div style={{ width: '100%', height: 190 }}>
            <ResponsiveContainer>
              <AreaChart data={lineData}>
                <defs>
                  <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7090f5" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#7090f5" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" axisLine={false} tickLine={false} stroke="#94a3b8" fontSize={11} />
                <YAxis axisLine={false} tickLine={false} stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ background: '#fff', borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Area type="monotone" dataKey="val" stroke="#7090f5" strokeWidth={3} fillOpacity={1} fill="url(#colorVal)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Double Bar Chart */}
        <div className="dash-card">
          <div className="dash-card-header">
            <span className="dash-card-title">Bar Chart</span>
          </div>
          <div style={{ width: '100%', height: 190 }}>
            <ResponsiveContainer>
              <BarChart data={barData}>
                <XAxis dataKey="name" axisLine={false} tickLine={false} stroke="#94a3b8" fontSize={11} />
                <YAxis axisLine={false} tickLine={false} stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ background: '#fff', borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Bar dataKey="a" fill="#7090f5" radius={[4, 4, 0, 0]} />
                <Bar dataKey="b" fill="#c8b6ff" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pie Chart */}
        <div className="dash-card">
          <div className="dash-card-header">
            <span className="dash-card-title">Pie Chart</span>
          </div>
          <div style={{ width: '100%', height: 190, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ResponsiveContainer width="100%" height={170}>
              <PieChart>
                <Pie data={pieData} innerRadius={35} outerRadius={60} dataKey="value">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom 4 Soft Stat Cards Row matching Screenshot */}
      <div className="dashboard-grid">
        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div className="stat-icon blue">
            <FileText size={22} />
          </div>
          <div>
            <div className="stat-value">52</div>
            <div className="stat-label">Total Uploaded Notes</div>
          </div>
        </div>

        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div className="stat-icon purple">
            <Award size={22} />
          </div>
          <div>
            <div className="stat-value">88.4</div>
            <div className="stat-label">Average Note Score</div>
          </div>
        </div>

        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div className="stat-icon sky">
            <Clock size={22} />
          </div>
          <div>
            <div className="stat-value">1.2s</div>
            <div className="stat-label">Processing Time</div>
          </div>
        </div>
      </div>
    </div>
  );
}
