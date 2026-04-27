import React from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  width?: number;
}

export const Modal: React.FC<ModalProps> = ({ title, onClose, children, width = 420 }) => (
  <div style={{
    position: 'fixed', inset: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1000, backdropFilter: 'blur(4px)',
  }}>
    <div className="glass-panel" style={{ width, maxWidth: '95vw', padding: '2rem', maxHeight: '90vh', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }}>{title}</h2>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
          <X size={22} />
        </button>
      </div>
      {children}
    </div>
  </div>
);
