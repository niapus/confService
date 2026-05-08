const { useState, useEffect, useRef } = React;

function getCsrfToken() {
   return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}

function ScheduleEditor() {
   const [conference, setConference] = useState(null);
   const [applications, setApplications] = useState([]);
   const [scheduleItems, setScheduleItems] = useState([]);
   const [usedApplicationIds, setUsedApplicationIds] = useState(new Set());
   const [loading, setLoading] = useState(true);
   const [dayModalOpen, setDayModalOpen] = useState(false);
   const [breakModalOpen, setBreakModalOpen] = useState(false);
   const [textModalOpen, setTextModalOpen] = useState(false);
   const [previewModalOpen, setPreviewModalOpen] = useState(false);
   const [notification, setNotification] = useState(null);
   const [editingItem, setEditingItem] = useState(null);
   const [dayForm, setDayForm] = useState({ date: '', title: '', startTime: '09:00' });
   const [breakForm, setBreakForm] = useState({ title: '', duration: 20 });
   const [textForm, setTextForm] = useState({ content: '' });
   const [editDayForm, setEditDayForm] = useState({ id: null, date: '', title: '', startTime: '09:00' });
   const [editBreakForm, setEditBreakForm] = useState({ id: null, title: '', duration: 20 });
   const [editTextForm, setEditTextForm] = useState({ id: null, content: '' });
   
   const draggedItemRef = useRef(null);

   const pathParts = window.location.pathname.split('/'); 
   const conferenceId = pathParts[pathParts.length - 2];

   useEffect(() => {
      if (!conferenceId) return;
      
      fetch(`/api/conferences/${conferenceId}/schedule-data`)
         .then(res => res.json())
         .then(data => {
            setConference(data.conference);
            setApplications(data.applications || []);
            setScheduleItems(data.schedule || []);
            
            const usedIds = new Set();
            (data.schedule || []).forEach(item => {
               if (item.item_type === 'talk' && item.application_id) {
                  usedIds.add(item.application_id);
               }
            });
            setUsedApplicationIds(usedIds);
            
            setLoading(false);
         })
         .catch(error => {
            console.error('Ошибка загрузки:', error);
            showNotification('Ошибка загрузки данных', 'error');
            setLoading(false);
         });
   }, [conferenceId]);

   const updateGlobalOrder = (items) => {
      return items.map((item, index) => ({ ...item, global_order: index + 1 }));
   };

   const recalculateSchedule = (items) => {
      let currentTime = null;
      
      return items.map(item => {
         if (item.item_type === 'day') {
            currentTime = new Date(`${item.day_date}T${item.day_start_time}:00`);
            return { ...item, start_time: null, end_time: null };
         }
         if (item.item_type === 'text') {
            return { ...item, start_time: null, end_time: null };
         }
         if ((item.item_type === 'talk' || item.item_type === 'break') && currentTime) {
            const duration = item.item_type === 'talk' ? item.talk_duration : item.break_duration;
            const startTime = new Date(currentTime);
            const endTime = new Date(currentTime);
            endTime.setMinutes(endTime.getMinutes() + duration);
            const newItem = { ...item, start_time: startTime.toISOString(), end_time: endTime.toISOString() };
            currentTime = endTime;
            return newItem;
         }
         return item;
      });
   };

   const updateSchedule = (newItems) => {
      const reordered = updateGlobalOrder(newItems);
      const recalculated = recalculateSchedule(reordered);
      setScheduleItems(recalculated);
   };

   const generateId = () => Date.now() + '_' + Math.random().toString(36).substr(2, 9);

   const formatTime = (isoString) => {
      if (!isoString) return '';
      const date = new Date(isoString);
      return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
   };

   const formatDate = (dateString) => {
      const date = new Date(dateString);
      const months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                     'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
      return `${date.getDate()} ${months[date.getMonth()]}`;
   };

   const getSpeakerName = (app) => {
      if (app.speaker_name) return app.speaker_name;
      if (app.surname) return `${app.surname} ${app.name}${app.patronymic ? ' ' + app.patronymic : ''}`;
      return app.name || 'Докладчик';
   };

   const getTalkTitle = (app) => {
      if (app.title) return app.title;
      if (app.theses && app.theses[0]) return app.theses[0].title;
      return 'Без названия';
   };

   const getTalkDuration = (app) => {
      if (app.duration_minutes) return app.duration_minutes;
      return conference?.performance_time || 15;
   };

   const showNotification = (message, type = 'success') => {
      setNotification({ message, type });
      setTimeout(() => setNotification(null), 3000);
   };

   const handleDragStart = (e, type, data) => {
      draggedItemRef.current = { type, data };
      e.dataTransfer.setData('type', type);
      e.target.closest('.application-card')?.classList.add('dragging');
      e.target.closest('.schedule-item')?.classList.add('dragging');
   };

   const handleDragEnd = () => {
      document.querySelectorAll('.dragging').forEach(el => el.classList.remove('dragging'));
      document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
      draggedItemRef.current = null;
   };

   const handleDragOver = (e) => {
      e.preventDefault();
      const element = e.target.closest('.schedule-item');
      if (element) element.classList.add('drag-over');
   };

   const handleDragLeave = (e) => {
      const element = e.target.closest('.schedule-item');
      if (element) element.classList.remove('drag-over');
   };

   const handleDrop = (e) => {
      e.preventDefault();
      const targetElement = e.target.closest('.schedule-item');
      targetElement?.classList.remove('drag-over');
      
      let targetIndex = scheduleItems.length;
      
      if (targetElement) {
         const targetId = targetElement.getAttribute('data-schedule-id');
         targetIndex = scheduleItems.findIndex(item => item.id == targetId);
         targetIndex = targetIndex + 1;
      }
      
      if (!draggedItemRef.current) return;
      
      if (draggedItemRef.current.type === 'application') {
         const app = draggedItemRef.current.data;
         
         if (usedApplicationIds.has(app.id)) {
            showNotification('Эта заявка уже добавлена в расписание', 'error');
            return;
         }
         
         const newItem = {
            id: generateId(),
            item_type: 'talk',
            application_id: app.id,
            talk_speaker: getSpeakerName(app),
            talk_title: getTalkTitle(app),
            talk_duration: getTalkDuration(app),
            global_order: scheduleItems.length + 1
         };
         const newItems = [...scheduleItems];
         newItems.splice(targetIndex, 0, newItem);
         updateSchedule(newItems);
         
         setUsedApplicationIds(prev => new Set(prev).add(app.id));
         
         showNotification('Доклад добавлен в расписание', 'success');
      } 
      else if (draggedItemRef.current.type === 'schedule') {
         const draggedItem = draggedItemRef.current.data;
         const draggedIndex = scheduleItems.findIndex(item => item.id === draggedItem.id);
         let targetIdx = targetIndex;
         
         if (draggedIndex === targetIdx - 1) return;
         
         const newItems = [...scheduleItems];
         newItems.splice(draggedIndex, 1);
         if (draggedIndex < targetIdx) targetIdx--;
         newItems.splice(targetIdx, 0, draggedItem);
         updateSchedule(newItems);
         showNotification('Элемент перемещен', 'success');
      }
   };

   const addDay = (e) => {
      e.preventDefault();
      const dayNames = ['ВОСКРЕСЕНЬЕ', 'ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА'];
      const dayDate = new Date(dayForm.date);
      const dayName = dayNames[dayDate.getDay()];
      
      const newItem = {
         id: generateId(),
         item_type: 'day',
         day_date: dayForm.date,
         day_title: dayForm.title || `${formatDate(dayForm.date)}, ${dayName}`,
         day_start_time: dayForm.startTime,
         global_order: scheduleItems.length + 1
      };
      
      updateSchedule([...scheduleItems, newItem]);
      setDayModalOpen(false);
      setDayForm({ date: '', title: '', startTime: '09:00' });
      showNotification('День добавлен', 'success');
   };

   const addBreak = (e) => {
      e.preventDefault();
      const newItem = {
         id: generateId(),
         item_type: 'break',
         break_title: breakForm.title,
         break_duration: breakForm.duration,
         global_order: scheduleItems.length + 1
      };
      updateSchedule([...scheduleItems, newItem]);
      setBreakModalOpen(false);
      setBreakForm({ title: '', duration: 20 });
      showNotification('Перерыв добавлен', 'success');
   };

   const addText = (e) => {
      e.preventDefault();
      const newItem = {
         id: generateId(),
         item_type: 'text',
         text_content: textForm.content,
         global_order: scheduleItems.length + 1
      };
      updateSchedule([...scheduleItems, newItem]);
      setTextModalOpen(false);
      setTextForm({ content: '' });
      showNotification('Текстовый блок добавлен', 'success');
   };

   const deleteItem = (itemId) => {
      if (!confirm('Удалить этот элемент из расписания?')) return;
      
      const deletedItem = scheduleItems.find(item => item.id == itemId);
      const newItems = scheduleItems.filter(item => item.id != itemId);
      updateSchedule(newItems);
      
      if (deletedItem?.item_type === 'talk' && deletedItem.application_id) {
         setUsedApplicationIds(prev => {
            const newSet = new Set(prev);
            newSet.delete(deletedItem.application_id);
            return newSet;
         });
      }
      
      showNotification('Элемент удален', 'success');
   };

   const deleteDay = (itemId) => {
      if (!confirm('Удалить этот день и все доклады в нем?')) return;
      
      const deletedItem = scheduleItems.find(item => item.id == itemId);
      const deletedIndex = scheduleItems.findIndex(item => item.id == itemId);
      
      let itemsToDelete = [itemId];
      for (let i = deletedIndex + 1; i < scheduleItems.length; i++) {
         if (scheduleItems[i].item_type === 'day') break;
         itemsToDelete.push(scheduleItems[i].id);
      }
      
      const newItems = scheduleItems.filter(item => !itemsToDelete.includes(item.id));
      
      const freedApplicationIds = [];
      scheduleItems.forEach(item => {
         if (itemsToDelete.includes(item.id) && item.item_type === 'talk' && item.application_id) {
            freedApplicationIds.push(item.application_id);
         }
      });
      
      updateSchedule(newItems);
      
      setUsedApplicationIds(prev => {
         const newSet = new Set(prev);
         freedApplicationIds.forEach(id => newSet.delete(id));
         return newSet;
      });
      
      showNotification('День и все доклады в нем удалены', 'success');
   };

   const editItem = (item) => {
      if (item.item_type === 'day') {
         setEditDayForm({
            id: item.id,
            date: item.day_date,
            title: item.day_title,
            startTime: item.day_start_time
         });
      } else if (item.item_type === 'break') {
         setEditBreakForm({
            id: item.id,
            title: item.break_title,
            duration: item.break_duration
         });
      } else if (item.item_type === 'text') {
         setEditTextForm({
            id: item.id,
            content: item.text_content
         });
         return;
      }
      setEditingItem(item.item_type);
   };

   const saveEditDay = (e) => {
      e.preventDefault();
      const updatedItems = scheduleItems.map(item => {
         if (item.id === editDayForm.id) {
            return {
               ...item,
               day_date: editDayForm.date,
               day_title: editDayForm.title,
               day_start_time: editDayForm.startTime
            };
         }
         return item;
      });
      updateSchedule(updatedItems);
      setEditingItem(null);
      showNotification('День обновлен', 'success');
   };

   const saveEditBreak = (e) => {
      e.preventDefault();
      const updatedItems = scheduleItems.map(item => {
         if (item.id === editBreakForm.id) {
            return {
               ...item,
               break_title: editBreakForm.title,
               break_duration: editBreakForm.duration
            };
         }
         return item;
      });
      updateSchedule(updatedItems);
      setEditingItem(null);
      showNotification('Перерыв обновлен', 'success');
   };

   const saveEditText = (e) => {
      e.preventDefault();
      const updatedItems = scheduleItems.map(item => {
         if (item.id === editTextForm.id) {
            return {
               ...item,
               text_content: editTextForm.content
            };
         }
         return item;
      });
      updateSchedule(updatedItems);
      setEditingItem(null);
      showNotification('Текстовый блок обновлен', 'success');
   };

   const saveSchedule = () => {
      const data = {
         conference_id: conference?.id,
         schedule: scheduleItems
      };

      const headers = { 'Content-Type': 'application/json' };
      const csrfToken = getCsrfToken();
      if (csrfToken) {
         headers['X-CSRFToken'] = csrfToken;
      }

      fetch('/api/schedule', {
         method: 'POST',
         headers: headers,
         body: JSON.stringify(data)
      })
      .then(response => {
         if (response.ok) {
            showNotification('Расписание успешно сохранено!', 'success');
         } else {
            throw new Error('Ошибка сохранения');
         }
      })
      .catch(() => showNotification('Ошибка сохранения расписания', 'error'));
   };

   const copyToClipboard = () => {
      const data = { conference_id: conference?.id, schedule: scheduleItems };
      navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      showNotification('JSON скопирован в буфер обмена', 'success');
   };

   const renderPreview = () => {
      const previewItems = [];
      let currentDayItems = [];
      
      scheduleItems.forEach(item => {
         if (item.item_type === 'day') {
            if (currentDayItems.length > 0) {
               previewItems.push(React.createElement('div', { className: 'preview-day-group', key: previewItems.length },
                  React.createElement('h3', { className: 'preview-day-title' }, currentDayItems[0].day_title),
                  React.createElement('p', { className: 'preview-day-start' }, `Начало в ${currentDayItems[0].day_start_time}`),
                  currentDayItems.slice(1)
               ));
               currentDayItems = [];
            }
            currentDayItems.push(item);
         } else if (currentDayItems.length > 0) {
            if (item.item_type === 'talk') {
               currentDayItems.push(React.createElement('div', { className: 'preview-talk', key: item.id },
                  React.createElement('strong', null, `${formatTime(item.start_time)} – ${formatTime(item.end_time)}`),
                  React.createElement('div', null, item.talk_speaker),
                  React.createElement('div', null, item.talk_title)
               ));
            } else if (item.item_type === 'break') {
               currentDayItems.push(React.createElement('div', { className: 'preview-break', key: item.id },
                  React.createElement('strong', null, `${formatTime(item.start_time)} – ${formatTime(item.end_time)}`),
                  React.createElement('div', null, `☕ ${item.break_title}`)
               ));
            } else if (item.item_type === 'text') {
               currentDayItems.push(React.createElement('div', { className: 'preview-text', key: item.id },
                  item.text_content.split('\n').map((line, i) => React.createElement('span', { key: i }, line, React.createElement('br', null)))
               ));
            }
         }
      });
      
      if (currentDayItems.length > 0) {
         previewItems.push(React.createElement('div', { className: 'preview-day-group', key: previewItems.length },
            React.createElement('h3', { className: 'preview-day-title' }, currentDayItems[0].day_title),
            React.createElement('p', { className: 'preview-day-start' }, `Начало в ${currentDayItems[0].day_start_time}`),
            currentDayItems.slice(1)
         ));
      }
      
      if (previewItems.length === 0) {
         return React.createElement('p', null, 'Расписание пустое');
      }
      
      return previewItems;
   };

   if (loading) {
      return React.createElement('div', { className: 'loading' }, 'Загрузка...');
   }

   return React.createElement(
      'div',
      { className: 'schedule-editor' },
      React.createElement(
         'div',
         { className: 'applications-panel' },
         React.createElement('h3', null, 'Заявки для расписания'),
         React.createElement(
            'div',
            { className: 'applications-list' },
            applications.length === 0 
               ? React.createElement('p', { className: 'empty' }, 'Нет заявок для составления расписания')
               : applications
                  .filter(app => !usedApplicationIds.has(app.id))
                  .map(app =>
                  React.createElement(
                     'div',
                     {
                        key: app.id,
                        className: 'application-card',
                        draggable: true,
                        onDragStart: (e) => handleDragStart(e, 'application', app),
                        onDragEnd: handleDragEnd
                     },
                     React.createElement('div', { className: 'application-speaker' }, getSpeakerName(app)),
                     React.createElement('div', { className: 'application-title' }, getTalkTitle(app)),
                     React.createElement('div', { className: 'application-duration' }, `${getTalkDuration(app)} мин`)
                  )
               )
         ),
         React.createElement(
            'div',
            { className: 'toolbar' },
            React.createElement('button', { className: 'btn-add-day', onClick: () => setDayModalOpen(true) }, 'Добавить день'),
            React.createElement('button', { className: 'btn-add-break', onClick: () => setBreakModalOpen(true) }, 'Добавить поле с временным интервалом'),
            React.createElement('button', { className: 'btn-add-text', onClick: () => setTextModalOpen(true) }, 'Добавить поле без временного интервала'),
            React.createElement('button', { className: 'btn-save', onClick: saveSchedule }, 'Сохранить расписание')
         )
      ),
      React.createElement(
         'div',
         { className: 'schedule-panel' },
         React.createElement(
            'div',
            { className: 'schedule-header' },
            React.createElement('h2', null, 'Расписание конференции'),
            React.createElement('button', { className: 'btn-preview', onClick: () => setPreviewModalOpen(true) }, 'Предпросмотр')
         ),
         React.createElement(
            'div',
            { className: 'schedule-timeline' },
            scheduleItems.length === 0
               ? React.createElement('div', { className: 'empty-schedule' },
                  React.createElement('p', null, 'Расписание пока пустое'),
                  React.createElement('p', null, 'Добавьте день или перетащите заявку')
                 )
               : scheduleItems.map((item) => {
                  const timeDisplay = item.start_time && item.end_time ? `${formatTime(item.start_time)} – ${formatTime(item.end_time)}` : '';
                  let className = 'schedule-item';
                  let content = null;
                  
                  if (item.item_type === 'day') {
                     className += ' schedule-item-day';
                     content = React.createElement('div', { className: 'schedule-item-day' },
                        React.createElement('div', { className: 'schedule-item-header' },
                           React.createElement('span', { className: 'schedule-item-time' }, item.day_date),
                           React.createElement('div', { className: 'schedule-item-controls' },
                              React.createElement('button', { className: 'btn-edit', onClick: () => editItem(item) }, '✏️'),
                              React.createElement('button', { className: 'btn-delete', onClick: () => deleteDay(item.id) }, '🗑')
                           )
                        ),
                        React.createElement('div', { className: 'schedule-item-content' },
                           React.createElement('div', { className: 'schedule-item-title' }, item.day_title),
                           React.createElement('div', { className: 'schedule-item-meta' }, `Начало докладов: ${item.day_start_time}`)
                        )
                     );
                  } else if (item.item_type === 'talk') {
                     className += ' schedule-item-talk';
                     content = React.createElement('div', { className: 'schedule-item-talk' },
                        React.createElement('div', { className: 'schedule-item-header' },
                           React.createElement('span', { className: 'schedule-item-time' }, timeDisplay),
                           React.createElement('div', { className: 'schedule-item-controls' },
                              React.createElement('button', { className: 'btn-delete', onClick: () => deleteItem(item.id) }, '🗑')
                           )
                        ),
                        React.createElement('div', { className: 'schedule-item-content' },
                           React.createElement('div', { className: 'schedule-item-speaker' }, item.talk_speaker),
                           React.createElement('div', { className: 'schedule-item-title' }, item.talk_title),
                           React.createElement('div', { className: 'schedule-item-duration' }, `Длительность: ${item.talk_duration} мин`)
                        )
                     );
                  } else if (item.item_type === 'break') {
                     className += ' schedule-item-break';
                     content = React.createElement('div', { className: 'schedule-item-break' },
                        React.createElement('div', { className: 'schedule-item-header' },
                           React.createElement('span', { className: 'schedule-item-time' }, timeDisplay),
                           React.createElement('div', { className: 'schedule-item-controls' },
                              React.createElement('button', { className: 'btn-edit', onClick: () => editItem(item) }, '✏️'),
                              React.createElement('button', { className: 'btn-delete', onClick: () => deleteItem(item.id) }, '🗑')
                           )
                        ),
                        React.createElement('div', { className: 'schedule-item-content' },
                           React.createElement('div', { className: 'schedule-item-title' }, item.break_title),
                           React.createElement('div', { className: 'schedule-item-duration' }, `Длительность: ${item.break_duration} мин`)
                        )
                     );
                  } else if (item.item_type === 'text') {
                     className += ' schedule-item-text';
                     content = React.createElement('div', { className: 'schedule-item-text' },
                        React.createElement('div', { className: 'schedule-item-header' },
                           React.createElement('span', null, 'Текстовый блок'),
                           React.createElement('div', { className: 'schedule-item-controls' },
                              React.createElement('button', { className: 'btn-edit', onClick: () => editItem(item) }, '✏️'),
                              React.createElement('button', { className: 'btn-delete', onClick: () => deleteItem(item.id) }, '🗑')
                           )
                        ),
                        React.createElement('div', { className: 'schedule-item-content' },
                           React.createElement('div', { className: 'schedule-item-description' }, item.text_content)
                        )
                     );
                  }
                  
                  return React.createElement(
                     'div',
                     {
                        key: item.id,
                        className: className,
                        draggable: true,
                        'data-schedule-id': item.id,
                        onDragStart: (e) => handleDragStart(e, 'schedule', item),
                        onDragEnd: handleDragEnd,
                        onDragOver: handleDragOver,
                        onDragLeave: handleDragLeave,
                        onDrop: handleDrop
                     },
                     content
                  );
               })
         )
      ),
      editingItem === 'day' && React.createElement(
         'div',
         { className: 'modal active', onClick: () => setEditingItem(null) },
         React.createElement(
            'div',
            { className: 'modal-content', onClick: (e) => e.stopPropagation() },
            React.createElement('h3', null, 'Редактировать день'),
            React.createElement('form', { onSubmit: saveEditDay },
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Дата'),
                  React.createElement('input', { type: 'date', value: editDayForm.date, min: conference?.start_date, max: conference?.end_date, onChange: (e) => setEditDayForm({ ...editDayForm, date: e.target.value }), required: true })
               ),
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Заголовок дня'),
                  React.createElement('input', { type: 'text', value: editDayForm.title, onChange: (e) => setEditDayForm({ ...editDayForm, title: e.target.value }), required: true })
               ),
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Время начала докладов'),
                  React.createElement('input', { type: 'time', value: editDayForm.startTime, onChange: (e) => setEditDayForm({ ...editDayForm, startTime: e.target.value }), required: true })
               ),
               React.createElement('div', { className: 'modal-actions' },
                  React.createElement('button', { type: 'button', className: 'btn-secondary', onClick: () => setEditingItem(null) }, 'Отмена'),
                  React.createElement('button', { type: 'submit', className: 'btn-primary' }, 'Сохранить')
               )
            )
         )
      ),
      editingItem === 'break' && React.createElement(
         'div',
         { className: 'modal active', onClick: () => setEditingItem(null) },
         React.createElement(
            'div',
            { className: 'modal-content', onClick: (e) => e.stopPropagation() },
            React.createElement('h3', null, 'Редактировать перерыв'),
            React.createElement('form', { onSubmit: saveEditBreak },
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Название перерыва'),
                  React.createElement('input', { type: 'text', value: editBreakForm.title, onChange: (e) => setEditBreakForm({ ...editBreakForm, title: e.target.value }), required: true })
               ),
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Длительность (минут)'),
                  React.createElement('input', { type: 'number', value: editBreakForm.duration, min: 5, max: 180, onChange: (e) => setEditBreakForm({ ...editBreakForm, duration: parseInt(e.target.value) }), required: true })
               ),
               React.createElement('div', { className: 'modal-actions' },
                  React.createElement('button', { type: 'button', className: 'btn-secondary', onClick: () => setEditingItem(null) }, 'Отмена'),
                  React.createElement('button', { type: 'submit', className: 'btn-primary' }, 'Сохранить')
               )
            )
         )
      ),
      editingItem === 'text' && React.createElement(
         'div',
         { className: 'modal active', onClick: () => setEditingItem(null) },
         React.createElement(
            'div',
            { className: 'modal-content', onClick: (e) => e.stopPropagation() },
            React.createElement('h3', null, 'Редактировать текстовый блок'),
            React.createElement('form', { onSubmit: saveEditText },
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Текст'),
                  React.createElement('textarea', { value: editTextForm.content, onChange: (e) => setEditTextForm({ ...editTextForm, content: e.target.value }), rows: 4, required: true })
               ),
               React.createElement('div', { className: 'modal-actions' },
                  React.createElement('button', { type: 'button', className: 'btn-secondary', onClick: () => setEditingItem(null) }, 'Отмена'),
                  React.createElement('button', { type: 'submit', className: 'btn-primary' }, 'Сохранить')
               )
            )
         )
      ),
      React.createElement(
         'div',
         { className: `modal ${dayModalOpen ? 'active' : ''}`, onClick: () => setDayModalOpen(false) },
         React.createElement(
            'div',
            { className: 'modal-content', onClick: (e) => e.stopPropagation() },
            React.createElement('h3', null, 'Добавить новый день'),
            React.createElement('form', { onSubmit: addDay },
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Дата'),
                  React.createElement('input', { type: 'date', value: dayForm.date, min: conference?.start_date, max: conference?.end_date, onChange: (e) => setDayForm({ ...dayForm, date: e.target.value }), required: true })
               ),
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Заголовок дня'),
                  React.createElement('input', { type: 'text', value: dayForm.title, placeholder: '24 марта, ВТОРНИК', onChange: (e) => setDayForm({ ...dayForm, title: e.target.value }), required: true })
               ),
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Время начала докладов'),
                  React.createElement('input', { type: 'time', value: dayForm.startTime, onChange: (e) => setDayForm({ ...dayForm, startTime: e.target.value }), required: true })
               ),
               React.createElement('div', { className: 'modal-actions' },
                  React.createElement('button', { type: 'button', className: 'btn-secondary', onClick: () => setDayModalOpen(false) }, 'Отмена'),
                  React.createElement('button', { type: 'submit', className: 'btn-primary' }, 'Добавить')
               )
            )
         )
      ),
      React.createElement(
         'div',
         { className: `modal ${breakModalOpen ? 'active' : ''}`, onClick: () => setBreakModalOpen(false) },
         React.createElement(
            'div',
            { className: 'modal-content', onClick: (e) => e.stopPropagation() },
            React.createElement('h3', null, 'Добавить перерыв'),
            React.createElement('form', { onSubmit: addBreak },
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Название перерыва'),
                  React.createElement('input', { type: 'text', value: breakForm.title, onChange: (e) => setBreakForm({ ...breakForm, title: e.target.value }), required: true })
               ),
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Длительность (минут)'),
                  React.createElement('input', { type: 'number', value: breakForm.duration, min: 5, max: 180, onChange: (e) => setBreakForm({ ...breakForm, duration: parseInt(e.target.value) }), required: true })
               ),
               React.createElement('div', { className: 'modal-actions' },
                  React.createElement('button', { type: 'button', className: 'btn-secondary', onClick: () => setBreakModalOpen(false) }, 'Отмена'),
                  React.createElement('button', { type: 'submit', className: 'btn-primary' }, 'Добавить')
               )
            )
         )
      ),
      React.createElement(
         'div',
         { className: `modal ${textModalOpen ? 'active' : ''}`, onClick: () => setTextModalOpen(false) },
         React.createElement(
            'div',
            { className: 'modal-content', onClick: (e) => e.stopPropagation() },
            React.createElement('h3', null, 'Добавить текстовый блок'),
            React.createElement('form', { onSubmit: addText },
               React.createElement('div', { className: 'form-group' },
                  React.createElement('label', null, 'Текст'),
                  React.createElement('textarea', { value: textForm.content, onChange: (e) => setTextForm({ content: e.target.value }), rows: 4, required: true })
               ),
               React.createElement('div', { className: 'modal-actions' },
                  React.createElement('button', { type: 'button', className: 'btn-secondary', onClick: () => setTextModalOpen(false) }, 'Отмена'),
                  React.createElement('button', { type: 'submit', className: 'btn-primary' }, 'Добавить')
               )
            )
         )
      ),
      React.createElement(
         'div',
         { className: `modal ${previewModalOpen ? 'active' : ''}`, onClick: () => setPreviewModalOpen(false) },
         React.createElement(
            'div',
            { className: 'modal-content preview-modal', onClick: (e) => e.stopPropagation() },
            React.createElement('h3', null, 'Предпросмотр расписания'),
            React.createElement('div', { className: 'preview-content' }, renderPreview()),
            React.createElement('div', { className: 'modal-actions' },
               React.createElement('button', { className: 'btn-secondary', onClick: () => setPreviewModalOpen(false) }, 'Закрыть'),
               React.createElement('button', { className: 'btn-primary', onClick: copyToClipboard }, 'Копировать JSON')
            )
         )
      ),
      notification && React.createElement('div', { className: `notification ${notification.type}` }, notification.message)
   );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(ScheduleEditor));