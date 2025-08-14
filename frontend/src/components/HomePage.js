import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css';
import { getTeamScheduleForDate, getTaskDetails } from '../utils/api';

const HomePage = () => {
  const [teamPassword, setTeamPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [teamInfo, setTeamInfo] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [taskPopup, setTaskPopup] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const data = await getTeamScheduleForDate(teamPassword, selectedDate);

      if (data.success) {
        setTeamInfo(data);
        setError('');
      } else {
        setError(data.error || 'Nastala chyba');
        setTeamInfo(null);
      }
    } catch (err) {
      setError('Chyba pri pripojení k serveru');
      setTeamInfo(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdminAccess = () => {
    // Presmeruj na editáciu tímu
    if (teamInfo) {
      navigate(`/team-edit/${teamInfo.team_id || 'new'}`);
    }
  };

  const handleDateChange = async (newDate) => {
    if (!teamInfo || !teamPassword) return;

    setSelectedDate(newDate);
    setIsLoading(true);

    try {
      const data = await getTeamScheduleForDate(teamPassword, newDate);

      if (data.success) {
        setTeamInfo(data);
        setError('');
      } else {
        setError(data.error || 'Nastala chyba');
      }
    } catch (err) {
      setError('Chyba pri pripojení k serveru');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTaskClick = async (taskId) => {
    if (!teamPassword) return;

    try {
      const data = await getTaskDetails(taskId, teamPassword);

      if (data.success) {
        setTaskPopup(data.task);
      } else {
        setError(data.error || 'Nastala chyba');
      }
    } catch (err) {
      setError('Chyba pri pripojení k serveru');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('sk-SK', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getButtonLabels = (currentDate) => {
    const today = new Date().toISOString().split('T')[0];
    const current = new Date(currentDate);
    const todayDate = new Date(today);

    if (currentDate === today) {
      return { prev: 'Včera', next: 'Zajtra' };
    } else if (current < todayDate) {
      return { prev: 'Predošlý deň', next: 'Ďalší deň' };
    } else {
      return { prev: 'Predošlý deň', next: 'Ďalší deň' };
    }
  };

  return (
    <div className="home-page">
      <div className="container">
        <h1 className="main-title">Systém Rozdelenia Úloh</h1>

        {!teamInfo ? (
          <div className="login-section">
            <h2>Zadajte heslo tímu</h2>
            <form onSubmit={handleSubmit} className="login-form">
              <div className="form-group">
                <input
                  type="text"
                  value={teamPassword}
                  onChange={(e) => setTeamPassword(e.target.value)}
                  placeholder="Heslo tímu"
                  className="form-input"
                  required
                />
              </div>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={isLoading}
              >
                {isLoading ? 'Načítavam...' : 'Prihlásiť sa'}
              </button>
            </form>

            {error && <div className="error-message">{error}</div>}

            <div className="admin-link">
              <a href="/admin" className="admin-link-text">
                Admin rozhranie →
              </a>
            </div>
          </div>
        ) : (
          <div className="team-info">
            <div className="team-header">
              <h2>Tím: {teamInfo.team_name}</h2>
              <div className="admin-actions">
                <button 
                  onClick={handleAdminAccess}
                  className="btn btn-secondary"
                >
                  Editovať tím
                </button>
              </div>
            </div>

                        <div className="schedule-section">
              <div className="schedule-header">
                <h3>Rozvrh úloh</h3>
                <div className="date-selector">
                  <button 
                    onClick={() => handleDateChange(new Date(new Date(teamInfo.date).getTime() - 86400000).toISOString().split('T')[0])}
                    className="btn btn-small btn-outline"
                    disabled={isLoading}
                  >
                    ← {getButtonLabels(teamInfo.date).prev}
                  </button>
                  <span className="current-date">
                    {formatDate(teamInfo.date)}
                  </span>
                  <button 
                    onClick={() => handleDateChange(new Date(new Date(teamInfo.date).getTime() + 86400000).toISOString().split('T')[0])}
                    className="btn btn-small btn-outline"
                    disabled={isLoading}
                  >
                    {getButtonLabels(teamInfo.date).next} →
                  </button>
                </div>
              </div>

              {teamInfo.schedules && teamInfo.schedules.length > 0 ? (
                <div className="schedule-list">
                  {(() => {
                    const sortedSchedules = teamInfo.schedules
                      .sort((a, b) => (a.time_slot || 1) - (b.time_slot || 1));

                    const schedulesBySlot = {};
                    sortedSchedules.forEach(schedule => {
                      const slot = schedule.time_slot || 1;
                      if (!schedulesBySlot[slot]) {
                        schedulesBySlot[slot] = [];
                      }
                      schedulesBySlot[slot].push(schedule);
                    });

                    return Object.keys(schedulesBySlot).sort((a, b) => parseInt(a) - parseInt(b)).map(slot => (
                      <div key={`slot-${slot}`} className="time-slot-group">
                        <h4 className="time-slot-title">Časový slot {slot}</h4>
                        {schedulesBySlot[slot].map((schedule) => (
                          <div 
                            key={schedule.id} 
                            className={`schedule-item ${schedule.task_description ? 'clickable' : ''}`}
                            data-time-slot={schedule.time_slot || 1}
                            onClick={() => schedule.task_description && handleTaskClick(schedule.task_id)}
                          >
                            <div className="schedule-header">
                              <div className="schedule-task">{schedule.task}</div>
                              <div className="schedule-time-slot">Slot {schedule.time_slot || 1}</div>
                            </div>
                            <div className="schedule-members">
                              {schedule.members.map((member, index) => (
                                <span key={index} className="member">{member}</span>
                              ))}
                              {schedule.members.length > 1 && (
                                <span className="separator">+</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ));
                  })()}
                </div>
              ) : (
                <div className="no-schedules">
                  <p>{teamInfo.message || 'Pre tento deň nie je vygenerovaný rozvrh úloh.'}</p>
                  <p>Kontaktujte vedúceho tímu pre vytvorenie rozvrhu.</p>
                </div>
              )}
            </div>

            <button 
              onClick={() => {
                setTeamInfo(null);
                setTeamPassword('');
              }}
              className="btn btn-outline"
            >
              Odhlásiť sa
            </button>
          </div>
        )}

        {/* Task Detail Popup */}
        {taskPopup && (
          <div className="popup-overlay" onClick={() => setTaskPopup(null)}>
            <div className="popup-content" onClick={(e) => e.stopPropagation()}>
              <div className="popup-header">
                <h3>{taskPopup.name}</h3>
                <button 
                  className="popup-close"
                  onClick={() => setTaskPopup(null)}
                >
                  ×
                </button>
              </div>
              <div className="popup-body">
                {taskPopup.description && (
                  <div className="task-description">
                    <h4>Popis úlohy:</h4>
                    <p>{taskPopup.description}</p>
                  </div>
                )}
                <div className="task-details">
                  <div className="detail-item">
                    <span className="detail-label">Potrebných ľudí:</span>
                    <span className="detail-value">{taskPopup.people_needed}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

};

export default HomePage;
