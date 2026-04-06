const { useState, useEffect } = React;

function StatsCard({ title, value }) {
   return React.createElement(
      'div',
      { className: 'stat-card' },
      React.createElement('div', { className: 'stat-value' }, value),
      React.createElement('div', { className: 'stat-label' }, title)
   );
}

function ApplicationRow({ application }) {
   const hasTheses = application.theses && application.theses.length > 0;

   return React.createElement(
      'tr',
      null,
      React.createElement(
         'td',
         null,
         React.createElement('strong', null, application.full_name),
         React.createElement(
            'div',
            { className: 'badges' },
            application.is_student && React.createElement('span', { className: 'badge student-badge' }, 'Студент'),
            application.is_worker && React.createElement('span', { className: 'badge worker-badge' }, 'Работник')
         )
      ),
      React.createElement('td', null, application.email),
      React.createElement('td', null, `${application.birth_date}(${application.age})`),
      React.createElement(
         'td',
         null,
         application.degree === 'none' ? 'Нет' :
         application.degree === 'candidate' ? 'Кандидат наук' : 'Доктор наук'
      ),
      React.createElement(
         'td',
         null,
         application.is_worker ? 'Работник' :
         application.is_student ? 'Студент' : '—'
      ),
      React.createElement(
         'td',
         null,
         React.createElement(
            'span',
            { className: `format-badge ${application.participation_format}` },
            application.participation_format === 'offline' ? 'Очно' : 'Онлайн'
         )
      ),
      React.createElement(
         'td',
         null,
         hasTheses ? React.createElement(
            'div',
            null,
            application.theses.map((thesis, index) =>
               React.createElement(
                  'div',
                  { style: { marginBottom: index < application.theses.length - 1 ? '15px' : '0', padding: 0 } },
                  React.createElement('strong', null,
                     application.theses.length === 1 ? thesis.title : `${index + 1}. ${thesis.title}`
                  ),
                  React.createElement(
                     'div',
                     { className: `status-badge ${thesis.status}` },
                     thesis.status === 'pending' && '⏳ На рассмотрении',
                     thesis.status === 'accepted' && '✅ Принят',
                     thesis.status === 'rejected' && '❌ Отклонён'
                  )
               )
            )
         ) : React.createElement('div', null, 'Нет тезисов')
      ),
      React.createElement(
         'td',
         null,
         hasTheses && React.createElement(
            'div',
            null,
            application.theses.map((thesis, index) =>
               React.createElement(
                  'button',
                  {
                     className: 'action-btn',
                     onClick: () => window.location.href = `/admin/applications/${thesis.id}`,
                     style: {
                        marginBottom: index < application.theses.length - 1 ? '20px' : '0',
                     }
                  },
                  application.theses.length === 1 ? '👁️' : `👁️ Тезис №${index + 1}`
               )
            )
         )
      )
   );
}


function ConferenceApp() {
   const pathParts = window.location.pathname.split('/');
   const conferenceId = pathParts[pathParts.length - 1];
   const [applications, setApplications] = useState([]);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   const [filters, setFilters] = useState({
      search: '',
      format: 'all',
      thesis: 'all',
      status: 'all'
   });

   useEffect(() => {
      fetch(`/admin/api/conferences/${conferenceId}`)
         .then(res => {
            if (!res.ok) throw new Error('Ошибка загрузки');
            return res.json();
         })
         .then(data => {
            setApplications(data.applications);
            setLoading(false);
         })
         .catch(err => {
            setError(err.message);
            setLoading(false);
         });
   }, [conferenceId]);

   const filteredApplications = applications.filter(app => {
      const searchLower = filters.search.toLowerCase();
      const fullName = `${app.surname} ${app.name} ${app.patronymic || ''}`;
      const matchesSearch = !filters.search ||
         fullName.toLowerCase().includes(searchLower) ||
         app.email.toLowerCase().includes(searchLower);

      const matchesFormat = filters.format === 'all' ||
         app.participation_format === filters.format;

      const hasThesis = app.theses && app.theses.length > 0;
      const matchesThesis = filters.thesis === 'all' ||
         (filters.thesis === 'with' && hasThesis) ||
         (filters.thesis === 'without' && !hasThesis);

      const thesisStatus = hasThesis ? app.theses[0].status : 'none';
      const matchesStatus = filters.status === 'all' ||
         (hasThesis && app.theses.some(thesis => thesis.status === filters.status));

      return matchesSearch && matchesFormat && matchesThesis && matchesStatus;
   });

   const stats = {
      total: applications.length,
      withThesis: applications.filter(app => app.theses && app.theses.length > 0).length,
      students: applications.filter(app => app.is_student).length,
      workers: applications.filter(app => app.is_worker).length,
      offline: applications.filter(app => app.participation_format === 'offline').length,
      online: applications.filter(app => app.participation_format === 'online').length
   };

   if (error) return React.createElement('div', { className: 'error' }, `Ошибка: ${error}`);

   return React.createElement(
      'div',
      { className: 'conference-detail' },
      React.createElement(
         'h1', null,
         React.createElement('a', { href: '/admin', style: { textDecoration: 'none', color: 'inherit' }}, '← На главную'),
         ` | Конференция #${conferenceId}`
      ),

      React.createElement(
         'div',
         { className: 'stats-grid' },
         React.createElement(StatsCard, { title: 'Всего заявок', value: stats.total }),
         React.createElement(StatsCard, { title: 'С тезисами', value: stats.withThesis }),
         React.createElement(StatsCard, { title: 'Студентов', value: stats.students }),
         React.createElement(StatsCard, { title: 'Работников', value: stats.workers }),
         React.createElement(StatsCard, { title: 'Очно', value: stats.offline }),
         React.createElement(StatsCard, { title: 'Онлайн', value: stats.online })
      ),

      React.createElement(
         'div',
         { className: 'filters' },
         React.createElement('input', {
            type: 'text',
            placeholder: '🔍 Поиск по ФИО или email...',
            className: 'filter-input',
            value: filters.search,
            onChange: (e) => setFilters({...filters, search: e.target.value})
         }),
         React.createElement(
            'select',
            {
               className: 'filter-select',
               value: filters.format,
               onChange: (e) => setFilters({...filters, format: e.target.value})
            },
            React.createElement('option', { value: 'all' }, 'Все форматы'),
            React.createElement('option', { value: 'offline' }, 'Очно'),
            React.createElement('option', { value: 'online' }, 'Онлайн')
         ),
         React.createElement(
            'select',
            {
               className: 'filter-select',
               value: filters.thesis,
               onChange: (e) => setFilters({...filters, thesis: e.target.value})
            },
            React.createElement('option', { value: 'all' }, 'Все заявки'),
            React.createElement('option', { value: 'with' }, 'С тезисами'),
            React.createElement('option', { value: 'without' }, 'Без тезисов')
         ),
         React.createElement(
            'select',
            {
               className: 'filter-select',
               value: filters.status,
               onChange: (e) => setFilters({...filters, status: e.target.value})
            },
            React.createElement('option', { value: 'all' }, 'Все статусы'),
            React.createElement('option', { value: 'pending' }, 'На рассмотрении'),
            React.createElement('option', { value: 'accepted' }, 'Принято'),
            React.createElement('option', { value: 'rejected' }, 'Отклонено')
         )
      ),

      React.createElement('div', { className: 'filter-info' }, `Показано ${filteredApplications.length} из ${applications.length} заявок`),

      React.createElement(
         'div',
         { className: 'table-container' },
         React.createElement(
            'table',
            { className: 'applications-table' },
            React.createElement(
               'thead',
               null,
               React.createElement(
                  'tr',
                  null,
                  React.createElement('th', null, 'ФИО'),
                  React.createElement('th', null, 'Email'),
                  React.createElement('th', null, 'Дата рождения'),
                  React.createElement('th', null, 'Степень'),
                  React.createElement('th', null, 'Статус'),
                  React.createElement('th', null, 'Формат'),
                  React.createElement('th', null, 'Доклад'),
                  React.createElement('th', null, 'Действия')
               )
            ),
            React.createElement(
               'tbody',
               null,
               filteredApplications.map(app => React.createElement(ApplicationRow, { key: app.id, application: app }))
            )
         )
      )
   );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(ConferenceApp));