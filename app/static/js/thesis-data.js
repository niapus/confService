function updateStatus(status) {
   if (confirm(`Вы уверены, что хотите ${status === 'accepted' ? 'принять' : 'отклонить'} этот тезис?`)) {
      fetch(`/admin/theses/{{ thesis.id }}/status`, {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
         },
         body: JSON.stringify({ status: status })
      })
      .then(response => {
         if (response.ok) {
            window.location.reload();
         } else {
            alert('Произошла ошибка при обновлении статуса');
         }
      })
      .catch(error => {
         console.error('Error:', error);
         alert('Произошла ошибка при обновлении статуса');
      });
   }
}