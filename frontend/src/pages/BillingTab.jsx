import React from 'react';
import { CreditCard, AlertCircle } from 'lucide-react';
import CreditTracker from '../components/CreditTracker';

function BillingTab() {
  return (
    <div>
      <div className="page-header">
        <h1>Billing</h1>
        <p>Monitor your credit usage and invoicing details</p>
      </div>

      {/* Credit Usage Section */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <CreditCard size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
            Credit Usage
          </h3>
        </div>
        <div style={{ padding: '1.5rem' }}>
          <CreditTracker />
        </div>
      </div>

      {/* Credit Rate Info */}
      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">Credit Rate Information</h3>
        </div>
        <div style={{ padding: '1.5rem' }}>
          <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
            Credits are calculated based on the following activities:
          </p>
          
          <table className="table" style={{ marginBottom: '1.5rem' }}>
            <thead>
              <tr>
                <th>Action</th>
                <th>Credits</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Research brand website</td>
                <td>10 credits</td>
              </tr>
              <tr>
                <td>Add new brand to database</td>
                <td>5 credits</td>
              </tr>
              <tr>
                <td>Monthly brand update check</td>
                <td>2 credits per brand</td>
              </tr>
              <tr>
                <td>Weekly new brand discovery</td>
                <td>20 credits per run</td>
              </tr>
              <tr>
                <td>API call (TikTok/Instagram)</td>
                <td>1 credit per call</td>
              </tr>
            </tbody>
          </table>

          <div style={{
            background: 'rgba(79, 70, 229, 0.1)',
            padding: '1rem',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}>
            <CreditCard size={20} style={{ color: 'var(--primary-color)' }} />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                1 Credit = $0.10 USD
              </div>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                Credits are invoiced monthly based on usage
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Invoice Note */}
      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        background: 'rgba(245, 158, 11, 0.1)',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        border: '1px solid rgba(245, 158, 11, 0.2)'
      }}>
        <AlertCircle size={20} style={{ color: 'var(--warning)' }} />
        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
            Invoicing
          </div>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Invoices are generated on the 1st of each month based on your credit usage.
          </div>
        </div>
      </div>
    </div>
  );
}

export default BillingTab;
