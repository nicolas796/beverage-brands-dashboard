import React, { useState, useEffect } from 'react';
import { CreditCard, AlertCircle } from 'lucide-react';

// Credit conversion: 1 credit = $0.10
const CREDIT_VALUE = 0.10;
const DEFAULT_CREDIT_BUDGET = 1000; // 1000 credits default

function CreditTracker() {
  const [creditsUsed, setCreditsUsed] = useState(0);
  const [creditBudget, setCreditBudget] = useState(DEFAULT_CREDIT_BUDGET);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCreditData();
  }, []);

  const loadCreditData = async () => {
    try {
      setLoading(true);
      
      // Fetch usage data from backend
      const usageResponse = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/credits/usage?days=30`);
      if (!usageResponse.ok) throw new Error('Failed to load usage data');
      const usageData = await usageResponse.json();
      
      // Convert dollar amount to credits
      const totalCost = usageData?.stats?.total_cost || 0;
      const calculatedCredits = Math.round(totalCost / CREDIT_VALUE);
      setCreditsUsed(calculatedCredits);
      
      // Fetch budget data
      const budgetResponse = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/credits/budget`);
      if (budgetResponse.ok) {
        const budgetData = await budgetResponse.json();
        // Convert dollar budget to credits
        const budgetDollars = budgetData.monthly_budget || 100;
        setCreditBudget(Math.round(budgetDollars / CREDIT_VALUE));
      }
      
      setError(null);
    } catch (err) {
      setError(err.message);
      // Fallback: use mock data for demo
      setCreditsUsed(420);
      setCreditBudget(1000);
    } finally {
      setLoading(false);
    }
  };

  // Calculate percentage
  const percentUsed = Math.min((creditsUsed / creditBudget) * 100, 100);

  // Calculate progress bar color
  const getProgressColor = () => {
    if (percentUsed < 50) return '#10b981'; // Green
    if (percentUsed < 80) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  // Calculate equivalent cost
  const costEquivalent = (creditsUsed * CREDIT_VALUE).toFixed(2);

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
        Loading credit data...
      </div>
    );
  }

  if (error && creditsUsed === 0) {
    return (
      <div style={{ 
        padding: '1rem', 
        background: '#fee2e2', 
        borderRadius: '8px',
        color: '#dc2626',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        <AlertCircle size={20} />
        Error loading credit data: {error}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Main Credit Card */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '16px',
        padding: '1.5rem',
        color: 'white',
        boxShadow: '0 10px 25px rgba(102, 126, 234, 0.3)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <CreditCard size={24} />
          <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>
            Credits Used This Month
          </h2>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '1rem' }}>
          <span style={{ fontSize: '3rem', fontWeight: 700 }}>
            {creditsUsed}
          </span>
          <span style={{ fontSize: '1.25rem', opacity: 0.8 }}>
            of {creditBudget} credits
          </span>
        </div>

        {/* Progress Bar */}
        <div style={{ 
          width: '100%', 
          height: '12px', 
          background: 'rgba(255,255,255,0.3)', 
          borderRadius: '6px',
          overflow: 'hidden',
          marginBottom: '0.75rem'
        }}>
          <div style={{
            width: `${percentUsed}%`,
            height: '100%',
            background: getProgressColor(),
            borderRadius: '6px',
            transition: 'width 0.5s ease'
          }} />
        </div>

        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          fontSize: '0.875rem',
          opacity: 0.9
        }}>
          <span>{percentUsed.toFixed(1)}% used</span>
          <span>{creditBudget - creditsUsed} credits remaining</span>
        </div>

        {percentUsed >= 100 && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem',
            background: 'rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.9rem'
          }}>
            <AlertCircle size={16} />
            You've exceeded your monthly credit budget!
          </div>
        )}
      </div>

      {/* Cost Equivalent */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '1.25rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        border: '1px solid var(--border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
            Equivalent Cost
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            ${costEquivalent} USD
          </div>
        </div>
        <div style={{
          fontSize: '0.75rem',
          color: 'var(--text-secondary)',
          textAlign: 'right'
        }}>
          <div>Rate: $0.10/credit</div>
          <div>Invoiced monthly</div>
        </div>
      </div>

      {/* Refresh Button */}
      <div style={{ textAlign: 'right' }}>
        <button 
          onClick={loadCreditData}
          style={{
            padding: '0.5rem 1rem',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.875rem',
            color: 'var(--text-primary)'
          }}
        >
          Refresh Data
        </button>
      </div>
    </div>
  );
}

export default CreditTracker;
