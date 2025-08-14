import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './TeamEditPage.css';

const TeamEditPage = () => {
  const { teamId } = useParams();
  const navigate = useNavigate();
  
  const [adminPassword, setAdminPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [teamInfo, setTeamInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Formuláre
  const [newMemberName, setNewMemberName] = useState('');
  const [newTaskName, setNewTaskName] = useState('');
  const [newTaskDescription, setNewTaskDescription] = useState('');
  const [newTaskPeopleNeeded, setNewTaskPeopleNeeded] = useState(1);
  const [newTaskTimeSlot, setNewTaskTimeSlot] = useState(1);
  const [scheduleDate, setScheduleDate] = useState(new Date().toISOString().split('T')[0]);
  const [importMembersText, setImportMembersText] = useState('');
  const [editingMember, setEditingMember] = useState(null);
  const [editMemberName, setEditMemberName] = useState('');
  const [importTasksText, setImportTasksText] = useState('');
  const [editingTask, setEditingTask] = useState(null);
  const [editTaskName, setEditTaskName] = useState('');
  const [editTaskDescription, setEditTaskDescription] = useState('');
  const [editTaskPeopleNeeded, setEditTaskPeopleNeeded] = useState(1);
  const [editTaskTimeSlot, setEditTaskTimeSlot] = useState(1);
  
  // Loading states
  const [isAddingMember, setIsAddingMember] = useState(false);
  const [isAddingTask, setIsAddingTask] = useState(false);
  const [isGeneratingSchedule, setIsGeneratingSchedule] = useState(false);

  const loadTeamInfo = useCallback(async () => {
    try {
      const response = await fetch(`/api/team-info/${teamId}/`);
      const data = await response.json();
      
      if (data.success) {
        setTeamInfo(data);
      } else {
        setError(data.error || 'Nepodarilo sa načítať informácie o tíme');
      }
    } catch (err) {
      setError('Chyba pri načítaní tímu');
    }
  }, [teamId]);

  useEffect(() => {
    if (teamId && teamId !== 'new') {
      loadTeamInfo();
    }
  }, [teamId, loadTeamInfo]);

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Pre admin prihlásenie do tímu používame admin heslo tímu
      // Toto heslo sa získa pri vytvorení tímu
      if (adminPassword.trim()) {
        setIsAuthenticated(true);
        setError('');
      } else {
        setError('Admin heslo je povinné');
      }
    } catch (err) {
      setError('Chyba pri pripojení');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!newMemberName.trim()) return;
    
    setIsAddingMember(true);
    setError('');

    try {
      const response = await fetch('/api/add-member/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team_id: teamId,
          admin_password: adminPassword,
          name: newMemberName.trim()
        }),
      });

      const data = await response.json();

      if (data.success) {
        setNewMemberName('');
        await loadTeamInfo(); // Obnov informácie o tíme
        setError('');
      } else {
        setError(data.error || 'Nastala chyba pri pridávaní člena');
      }
    } catch (err) {
      setError('Chyba pri pripojení k serveru');
    } finally {
      setIsAddingMember(false);
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!newTaskName.trim()) return;
    
    setIsAddingTask(true);
    setError('');

    try {
      const response = await fetch('/api/add-task/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team_id: teamId,
          admin_password: adminPassword,
          name: newTaskName.trim(),
          description: newTaskDescription.trim(),
          people_needed: newTaskPeopleNeeded,
          time_slot: newTaskTimeSlot
        }),
      });

      const data = await response.json();

      if (data.success) {
        setNewTaskName('');
        setNewTaskDescription('');
        setNewTaskTimeSlot(1);
        await loadTeamInfo(); // Obnov informácie o tíme
        setError('');
      } else {
        setError(data.error || 'Nastala chyba pri pridávaní úlohy');
      }
    } catch (err) {
      setError('Chyba pri pripojení k serveru');
    } finally {
      setIsAddingTask(false);
    }
  };

  const handleGenerateSchedule = async (e) => {
    e.preventDefault();
    if (!scheduleDate) {
      setError('Zadajte dátum');
      return;
    }
    
    setIsGeneratingSchedule(true);
    setError('');

    try {
      const response = await fetch('/api/generate-schedule/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team_id: teamId,
          admin_password: adminPassword,
          date: scheduleDate
        }),
      });

      const data = await response.json();

      if (data.success) {
        setError('');
        alert(`Rozvrh bol úspešne vygenerovaný pre ${data.message}!`);
        // Presmeruj na hlavnú stránku pre zobrazenie rozvrhu
        navigate('/');
      } else {
        setError(data.error || 'Nastala chyba pri generovaní rozvrhu');
      }
    } catch (err) {
      setError('Chyba pri pripojení k serveru');
    } finally {
      setIsGeneratingSchedule(false);
    }
  };

  const handleImportMembers = async () => {
    if (!importMembersText.trim()) {
      alert('Zadajte mená členov');
      return;
    }

    try {
      const response = await fetch('/api/import-members/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team_id: teamId,
          admin_password: adminPassword,
          members_text: importMembersText
        }),
      });

      const data = await response.json();

      if (data.success) {
        setImportMembersText('');
        loadTeamInfo();
        alert(`${data.message}\nPridaných: ${data.total_added}\nPreskočených: ${data.skipped}`);
      } else {
        alert(data.error || 'Chyba pri importovaní členov');
      }
    } catch (err) {
      alert('Chyba pri pripojení k serveru');
    }
  };

  const handleEditMember = (member) => {
    setEditingMember(member);
    setEditMemberName(member.name);
  };

  const handleUpdateMember = async () => {
    if (!editMemberName.trim()) {
      alert('Zadajte meno člena');
      return;
    }

    try {
      const response = await fetch('/api/update-member/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          member_id: editingMember.id,
          new_name: editMemberName.trim(),
          admin_password: adminPassword
        }),
      });

      const data = await response.json();

      if (data.success) {
        setEditingMember(null);
        setEditMemberName('');
        loadTeamInfo();
        alert(data.message);
      } else {
        alert(data.error || 'Chyba pri aktualizácii člena');
      }
    } catch (err) {
      alert('Chyba pri pripojení k serveru');
    }
  };

  const handleDeleteMember = async (member) => {
    if (!window.confirm(`Naozaj chcete vymazať člena ${member.name}?`)) {
      return;
    }

    try {
      const response = await fetch('/api/delete-member/', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          member_id: member.id,
          admin_password: adminPassword
        }),
      });

      const data = await response.json();

      if (data.success) {
        loadTeamInfo();
        alert(data.message);
      } else {
        alert(data.error || 'Chyba pri mazaní člena');
      }
    } catch (err) {
      alert('Chyba pri pripojení k serveru');
    }
  };

  const handleImportTasks = async () => {
    if (!importTasksText.trim()) {
      alert('Zadajte úlohy');
      return;
    }

    try {
      const response = await fetch('/api/import-tasks/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team_id: teamId,
          admin_password: adminPassword,
          tasks_text: importTasksText
        }),
      });

      const data = await response.json();

      if (data.success) {
        setImportTasksText('');
        loadTeamInfo();
        alert(`${data.message}\nPridaných: ${data.total_added}\nPreskočených: ${data.skipped}`);
      } else {
        alert(data.error || 'Chyba pri importovaní úloh');
      }
    } catch (err) {
      alert('Chyba pri pripojení k serveru');
    }
  };

  const handleEditTask = (task) => {
    setEditingTask(task);
    setEditTaskName(task.name);
    setEditTaskDescription(task.description || '');
    setEditTaskPeopleNeeded(task.people_needed);
    setEditTaskTimeSlot(task.time_slot || 1);
  };

  const handleUpdateTask = async () => {
    if (!editTaskName.trim()) {
      alert('Zadajte názov úlohy');
      return;
    }

    try {
      const response = await fetch('/api/update-task/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: editingTask.id,
          new_name: editTaskName.trim(),
          new_description: editTaskDescription.trim(),
          new_people_needed: editTaskPeopleNeeded,
          new_time_slot: editTaskTimeSlot,
          admin_password: adminPassword
        }),
      });

      const data = await response.json();

      if (data.success) {
        setEditingTask(null);
        setEditTaskName('');
        setEditTaskDescription('');
        setEditTaskPeopleNeeded(1);
        setEditTaskTimeSlot(1);
        loadTeamInfo();
        alert(data.message);
      } else {
        alert(data.error || 'Chyba pri aktualizácii úlohy');
      }
    } catch (err) {
      alert('Chyba pri pripojení k serveru');
    }
  };

  const handleDeleteTask = async (task) => {
    if (!window.confirm(`Naozaj chcete vymazať úlohu ${task.name}?`)) {
      return;
    }

    try {
      const response = await fetch('/api/delete-task/', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: task.id,
          admin_password: adminPassword
        }),
      });

      const data = await response.json();

      if (data.success) {
        loadTeamInfo();
        alert(data.message);
      } else {
        alert(data.error || 'Chyba pri mazaní úlohy');
      }
    } catch (err) {
      alert('Chyba pri pripojení k serveru');
    }
  };

  const handleRestoreTask = async (task) => {
    if (!window.confirm(`Naozaj chcete obnoviť úlohu ${task.name}?`)) {
      return;
    }

    try {
      const response = await fetch('/api/restore-task/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: task.id,
          admin_password: adminPassword
        }),
      });

      const data = await response.json();

      if (data.success) {
        loadTeamInfo();
        alert(data.message);
      } else {
        alert(data.error || 'Chyba pri obnovovaní úlohy');
      }
    } catch (err) {
      alert('Chyba pri pripojení k serveru');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="team-edit-page">
        <div className="container">
          <h1 className="main-title">Editácia Tímu</h1>
          
          <div className="login-section">
            <h2>Zadajte admin heslo pre tím</h2>
            <p className="login-note">
              Toto heslo ste dostali pri vytvorení tímu. Nie je to admin heslo aplikácie.
            </p>
            <form onSubmit={handleAdminLogin} className="login-form">
              <div className="form-group">
                <input
                  type="password"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  placeholder="Admin heslo pre tím"
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

  if (!teamInfo) {
    return (
      <div className="team-edit-page">
        <div className="container">
          <h1 className="main-title">Editácia Tímu</h1>
          <div className="loading">Načítavam informácie o tíme...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="team-edit-page">
      <div className="container">
        <h1 className="main-title">Editácia Tímu: {teamInfo.team.name}</h1>
        
        <div className="edit-content">
          {/* Pridanie člena */}
          <div className="section">
            <h2>Pridať člena tímu</h2>
            <form onSubmit={handleAddMember} className="edit-form">
              <div className="form-group">
                <label htmlFor="memberName">Meno člena:</label>
                <input
                  id="memberName"
                  type="text"
                  value={newMemberName}
                  onChange={(e) => setNewMemberName(e.target.value)}
                  placeholder="Zadajte meno člena"
                  className="form-input"
                  required
                />
              </div>
              
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={isAddingMember}
              >
                {isAddingMember ? 'Pridávam...' : 'Pridať člena'}
              </button>
            </form>
          </div>

          {/* Import členov */}
          <div className="section">
            <h2>Import členov z textu</h2>
            <div className="form-group">
              <label htmlFor="importMembers">Mená členov (jeden na riadok):</label>
              <textarea
                id="importMembers"
                value={importMembersText}
                onChange={(e) => setImportMembersText(e.target.value)}
                placeholder="Zadajte mená členov, každé na nový riadok:&#10;Ján&#10;Mária&#10;Peter&#10;Anna"
                className="form-textarea"
                rows="5"
              />
            </div>
            <button
              onClick={handleImportMembers}
              className="btn btn-secondary"
            >
              Import členov
            </button>
            <p className="help-text">
              Jeden člen na riadok. Duplicitné mená sa preskočia.
            </p>
          </div>

          {/* Pridanie úlohy */}
          <div className="section">
            <h2>Pridať úlohu</h2>
            <form onSubmit={handleAddTask} className="edit-form">
              <div className="form-group">
                <label htmlFor="taskName">Názov úlohy:</label>
                <input
                  id="taskName"
                  type="text"
                  value={newTaskName}
                  onChange={(e) => setNewTaskName(e.target.value)}
                  placeholder="Zadajte názov úlohy"
                  className="form-input"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="taskDescription">Popis úlohy:</label>
                <textarea
                  id="taskDescription"
                  value={newTaskDescription}
                  onChange={(e) => setNewTaskDescription(e.target.value)}
                  placeholder="Zadajte popis úlohy (voliteľné)"
                  className="form-textarea"
                  rows="3"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="taskPeopleNeeded">Počet potrebných ľudí:</label>
                <input
                  id="taskPeopleNeeded"
                  type="number"
                  value={newTaskPeopleNeeded}
                  onChange={(e) => setNewTaskPeopleNeeded(parseInt(e.target.value))}
                  min="1"
                  max="10"
                  className="form-input"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="taskTimeSlot">Časový slot:</label>
                <select
                  id="taskTimeSlot"
                  value={newTaskTimeSlot}
                  onChange={(e) => setNewTaskTimeSlot(parseInt(e.target.value))}
                  className="form-input"
                  required
                >
                  <option value={1}>Slot 1</option>
                  <option value={2}>Slot 2</option>
                  <option value={3}>Slot 3</option>
                  <option value={4}>Slot 4</option>
                  <option value={5}>Slot 5</option>
                </select>
              </div>
              
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={isAddingTask}
              >
                {isAddingTask ? 'Pridávam...' : 'Pridať úlohy'}
              </button>
            </form>
          </div>

          {/* Import úloh */}
          <div className="section">
            <h2>Import úloh z textu</h2>
            <div className="form-group">
              <label htmlFor="importTasks">Úlohy (formát: Názov (X) - Popis):</label>
              <textarea
                id="importTasks"
                value={importTasksText}
                onChange={(e) => setImportTasksText(e.target.value)}
                placeholder="Zadajte úlohy, každú na nový riadok:&#10;Frontend (2) - Vývoj UI - 1&#10;Backend (1) - API a databáza - 2&#10;Testovanie (2) - QA a testy - 3"
                className="form-textarea"
                rows="5"
              />
            </div>
            <button
              onClick={handleImportTasks}
              className="btn btn-secondary"
            >
              Import úloh
            </button>
            <p className="help-text">
              Formát: "Názov úlohy (X) - Popis - Časový slot" kde X je počet ľudí a časový slot je 1-5. Jeden riadok = jedna úloha.
            </p>
          </div>

          {/* Generovanie rozvrhu */}
          <div className="section">
            <h2>Vygenerovať rozvrh úloh</h2>
            <form onSubmit={handleGenerateSchedule} className="edit-form">
              <div className="form-group">
                <label htmlFor="scheduleDate">Dátum pre rozvrh:</label>
                <input
                  id="scheduleDate"
                  type="date"
                  value={scheduleDate}
                  onChange={(e) => setScheduleDate(e.target.value)}
                  className="form-input"
                  required
                />
              </div>
              
              <button 
                type="submit" 
                className="btn btn-success"
                disabled={isGeneratingSchedule || !teamInfo.members.length || !teamInfo.tasks.length}
              >
                {isGeneratingSchedule ? 'Generujem...' : 'Vygenerovať rozvrh'}
              </button>
              
              {(!teamInfo.members.length || !teamInfo.tasks.length) && (
                <div className="warning-message">
                  Pre generovanie rozvrhu je potrebné mať aspoň jedného člena a jednu úlohu.
                </div>
              )}
            </form>
          </div>

          {/* Zobrazenie aktuálneho stavu */}
          <div className="section">
            <h2>Aktuálny stav tímu</h2>
            
            <div className="status-grid">
              <div className="status-item">
                <h3>Členovia tímu ({teamInfo.members.length})</h3>
                {teamInfo.members.length > 0 ? (
                  <ul className="member-list">
                    {teamInfo.members.map(member => (
                      <li key={member.id} className="member-item">
                        {editingMember && editingMember.id === member.id ? (
                          <div className="member-edit">
                            <input
                              type="text"
                              value={editMemberName}
                              onChange={(e) => setEditMemberName(e.target.value)}
                              className="form-input member-edit-input"
                            />
                            <div className="member-actions">
                              <button
                                onClick={handleUpdateMember}
                                className="btn btn-small btn-success"
                              >
                                Uložiť
                              </button>
                              <button
                                onClick={() => {
                                  setEditingMember(null);
                                  setEditMemberName('');
                                }}
                                className="btn btn-small btn-outline"
                              >
                                Zrušiť
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="member-display">
                            <span className="member-name">{member.name}</span>
                            <div className="member-actions">
                              <button
                                onClick={() => handleEditMember(member)}
                                className="btn btn-small btn-outline"
                              >
                                Upraviť
                              </button>
                              <button
                                onClick={() => handleDeleteMember(member)}
                                className="btn btn-small btn-danger"
                              >
                                Vymazať
                              </button>
                            </div>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>Žiadni členovia</p>
                )}
              </div>
              
              <div className="status-item">
                <h3>Úlohy ({teamInfo.tasks.length})</h3>
                {teamInfo.tasks.length > 0 ? (
                  <ul className="task-list">
                    {teamInfo.tasks.map(task => (
                      <li key={task.id} className={`task-item ${task.is_deleted ? 'deleted-task' : ''}`}>
                        <div className="task-display">
                          <div className="task-header">
                            <strong className="task-name">{task.name}</strong>
                            <span className="task-people-count">({task.people_needed})</span>
                            <span className="task-time-slot">Slot {task.time_slot || 1}</span>
                            {task.is_deleted && <span className="task-deleted-badge">VYMAZANÁ</span>}
                          </div>
                          {task.description && <p className="task-description">{task.description}</p>}
                          <div className="task-actions">
                            {!task.is_deleted ? (
                              <>
                                <button
                                  onClick={() => handleEditTask(task)}
                                  className="btn btn-small btn-outline"
                                >
                                  Upraviť
                                </button>
                                <button
                                  onClick={() => handleDeleteTask(task)}
                                  className="btn btn-small btn-danger"
                                >
                                  Vymazať
                                </button>
                              </>
                            ) : (
                              <button
                                onClick={() => handleRestoreTask(task)}
                                className="btn btn-small btn-success"
                              >
                                Obnoviť
                              </button>
                            )}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>Žiadne úlohy</p>
                )}
              </div>
            </div>
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <div className="back-link">
            <a href="/" className="back-link-text">
              ← Späť na hlavnú stránku
            </a>
          </div>
        </div>
      </div>

      {/* Task Edit Popup */}
      {editingTask && (
        <div className="popup-overlay" onClick={() => setEditingTask(null)}>
          <div className="popup-content" onClick={(e) => e.stopPropagation()}>
            <div className="popup-header">
              <h3>Upraviť úlohu</h3>
              <button 
                className="popup-close"
                onClick={() => setEditingTask(null)}
              >
                ×
              </button>
            </div>
            <div className="popup-body">
              <div className="form-group">
                <label htmlFor="editTaskName">Názov úlohy:</label>
                <input
                  id="editTaskName"
                  type="text"
                  value={editTaskName}
                  onChange={(e) => setEditTaskName(e.target.value)}
                  className="form-input"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="editTaskDescription">Popis úlohy:</label>
                <textarea
                  id="editTaskDescription"
                  value={editTaskDescription}
                  onChange={(e) => setEditTaskDescription(e.target.value)}
                  className="form-textarea"
                  rows="3"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="editTaskPeopleNeeded">Počet potrebných ľudí:</label>
                <input
                  id="editTaskPeopleNeeded"
                  type="number"
                  value={editTaskPeopleNeeded}
                  onChange={(e) => setEditTaskPeopleNeeded(parseInt(e.target.value))}
                  min="1"
                  max="10"
                  className="form-input"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="editTaskTimeSlot">Časový slot:</label>
                <select
                  id="editTaskTimeSlot"
                  value={editTaskTimeSlot}
                  onChange={(e) => setEditTaskTimeSlot(parseInt(e.target.value))}
                  className="form-input"
                  required
                >
                  <option value={1}>Slot 1</option>
                  <option value={2}>Slot 2</option>
                  <option value={3}>Slot 3</option>
                  <option value={4}>Slot 4</option>
                  <option value={5}>Slot 5</option>
                </select>
              </div>
              
              <div className="popup-actions">
                <button
                  onClick={handleUpdateTask}
                  className="btn btn-success"
                >
                  Uložiť
                </button>
                <button
                  onClick={() => setEditingTask(null)}
                  className="btn btn-outline"
                >
                  Zrušiť
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamEditPage;
