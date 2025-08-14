import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './AdminPage.css';

const AdminPage = () => {
  const [adminPassword, setAdminPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [teamName, setTeamName] = useState('');
  const [isCreatingTeam, setIsCreatingTeam] = useState(false);
  const [createdTeam, setCreatedTeam] = useState(null);
  const navigate = useNavigate();

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/admin-login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ admin_password: adminPassword }),
      });

      const data = await response.json();

      if (data.success) {
        setIsAuthenticated(true);
        setError('');
      } else {
        setError(data.error || 'Nesprávne admin heslo');
      }
    } catch (err) {
      setError('Chyba pri pripojení k serveru');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTeam = async (e) => {
    e.preventDefault();
    setIsCreatingTeam(true);
    setError('');

    try {
      const response = await fetch('/api/create-team/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: teamName }),
      });

      const data = await response.json();

      if (data.success) {
        setCreatedTeam(data);
        setTeamName('');
        setError('');
      } else {
        setError(data.error || 'Nastala chyba pri vytváraní tímu');
      }
    } catch (err) {
      setError('Chyba pri pripojení k serveru');
    } finally {
      setIsCreatingTeam(false);
    }
  };

  const handleGoToTeamEdit = () => {
    if (createdTeam) {
      navigate(`/team-edit/${createdTeam.team_id}`);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="admin-page">
        <div className="container">
          <h1 className="main-title">Admin Rozhranie</h1>
          
          <div className="login-section">
            <h2>Zadajte admin heslo</h2>
            <form onSubmit={handleAdminLogin} className="login-form">
              <div className="form-group">
                <input
                  type="password"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  placeholder="Admin heslo"
                  className="form-input"
                  required
                />
              </div>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={isLoading}
              >
                {isLoading ? 'Prihlasujem...' : 'Prihlásiť sa'}
              </button>
            </form>
            
            {error && <div className="error-message">{error}</div>}
            
            <div className="back-link">
              <a href="/" className="back-link-text">
                ← Späť na hlavnú stránku
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="container">
        <h1 className="main-title">Admin Rozhranie</h1>
        
        <div className="admin-content">
          <div className="section">
            <h2>Vytvoriť nový tím</h2>
            
            {!createdTeam ? (
              <form onSubmit={handleCreateTeam} className="team-form">
                <div className="form-group">
                  <label htmlFor="teamName">Názov tímu:</label>
                  <input
                    id="teamName"
                    type="text"
                    value={teamName}
                    onChange={(e) => setTeamName(e.target.value)}
                    placeholder="Zadajte názov tímu"
                    className="form-input"
                    required
                  />
                </div>
                
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={isCreatingTeam}
                >
                  {isCreatingTeam ? 'Vytváram...' : 'Vytvoriť tím'}
                </button>
              </form>
            ) : (
              <div className="team-created">
                <h3>Tím bol úspešne vytvorený!</h3>
                
                <div className="team-credentials">
                  <div className="credential-item">
                    <strong>Heslo pre tím:</strong>
                    <span className="credential-value">{createdTeam.team_password}</span>
                  </div>
                  
                  <div className="credential-item">
                    <strong>Heslo pre admina:</strong>
                    <span className="credential-value">{createdTeam.admin_password}</span>
                  </div>
                </div>
                
                <div className="credential-note">
                  <p><strong>Dôležité:</strong> Uložte si tieto heslá! Budú potrebné pre správu tímu.</p>
                </div>
                
                <div className="action-buttons">
                  <button 
                    onClick={handleGoToTeamEdit}
                    className="btn btn-secondary"
                  >
                    Pokračovať v editácii tímu
                  </button>
                  
                  <button 
                    onClick={() => setCreatedTeam(null)}
                    className="btn btn-outline"
                  >
                    Vytvoriť ďalší tím
                  </button>
                </div>
              </div>
            )}
            
            {error && <div className="error-message">{error}</div>}
          </div>
          
          <div className="section">
            <h2>Existujúce tímy</h2>
            <p>Pre správu existujúcich tímov použite Django admin rozhranie:</p>
            <a href="/admin" className="btn btn-outline" target="_blank">
              Django Admin →
            </a>
          </div>
          
          <div className="back-link">
            <a href="/" className="back-link-text">
              ← Späť na hlavnú stránku
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
