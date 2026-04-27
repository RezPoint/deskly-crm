import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface ConfirmDialogProps {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmLabel?: string;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  message,
  onConfirm,
  onCancel,
  confirmLabel = 'Удалить',
}) => (
  <div style={{
    position: 'fixed', inset: 0,
    background: 'rgba(0,0,0,0.8)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1100, backdropFilter: 'blur(8px)',
  }}>
    <div className="glass-panel" style={{ width: 350, padding: '2rem', textAlign: 'center' }}>
      <AlertTriangle size={48} color="var(--danger)" style={{ margin: '0 auto 1rem' }} />
      <h2>{message}</h2>
      <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
        <button className="btn" style={{ flex: 1, background: 'var(--danger)', color: 'white' }} onClick={onConfirm}>
          {confirmLabel}
        </button>
        <button className="btn" style={{ flex: 1, background: 'rgba(255,255,255,0.1)' }} onClick={onCancel}>
          Отмена
        </button>
      </div>
    </div>
  </div>
);
