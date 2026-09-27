document.addEventListener('DOMContentLoaded', function() {
  // Mostrar fecha actual
  const fechaActual = new Date();
  document.getElementById('fecha-actual').textContent = fechaActual.toLocaleDateString('es-ES', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
  });

  // Variables globales
  let arqueoData = {};
  const calcularBtn = document.getElementById('calcular-arqueo');
  const guardarBtn = document.getElementById('guardar-arqueo');
  const loadingDiv = document.getElementById('loading');

  // Calcular arqueo
  calcularBtn.addEventListener('click', function(e) {
      e.preventDefault();
      
      const efectivoInicial = parseFloat(document.getElementById('monto-inicial').value);
      
      if (isNaN(efectivoInicial) {
          alert('Por favor ingresa un monto inicial válido');
          return;
      }

      // Mostrar loading
      loadingDiv.style.display = 'flex';
      calcularBtn.disabled = true;

      fetch("{% url 'tpv_shop:arqueo_automatico' %}", {
          method: 'POST',
          headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
          },
          body: `efectivo_inicial=${efectivoInicial}`
      })
      .then(response => {
          if (!response.ok) {
              throw new Error('Error en la respuesta del servidor');
          }
          return response.json();
      })
      .then(data => {
          if (data.error) {
              throw new Error(data.error);
          }

          arqueoData = data;
          
          // Actualizar UI
          document.getElementById('efectivo-teorico').textContent = `${data.efectivo_final.toFixed(2)} €`;
          document.getElementById('efectivo-contado').textContent = `${data.efectivo_inicial.toFixed(2)} €`;
          document.getElementById('total-ventas-efectivo').textContent = `${data.efectivo_final.toFixed(2)} €`;
          document.getElementById('total-ventas-tarjeta').textContent = `${data.tarjeta_total.toFixed(2)} €`;
          document.getElementById('total-ventas-bizum').textContent = `${data.bizum_total.toFixed(2)} €`;
          document.getElementById('total-ventas-dia').textContent = `${data.total_ventas.toFixed(2)} €`;
          
          // Calcular diferencia
          const diferencia = data.efectivo_final - data.efectivo_inicial;
          const diferenciaElement = document.getElementById('diferencia');
          diferenciaElement.textContent = `${Math.abs(diferencia).toFixed(2)} €`;
          
          if (diferencia < 0) {
              diferenciaElement.classList.add('negativo');
              diferenciaElement.classList.remove('positivo');
          } else if (diferencia > 0) {
              diferenciaElement.classList.add('positivo');
              diferenciaElement.classList.remove('negativo');
          } else {
              diferenciaElement.classList.remove('negativo', 'positivo');
          }

          // Habilitar botón de guardar
          guardarBtn.disabled = false;
      })
      .catch(error => {
          console.error('Error:', error);
          alert(error.message || 'Ocurrió un error al calcular el arqueo');
      })
      .finally(() => {
          loadingDiv.style.display = 'none';
          calcularBtn.disabled = false;
      });
  });

  // Guardar arqueo
  guardarBtn.addEventListener('click', function() {
      if (!arqueoData || Object.keys(arqueoData).length === 0) {
          alert('Primero debes calcular el arqueo');
          return;
      }

      guardarBtn.disabled = true;
      guardarBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Guardando...';

      // Agregar observaciones
      arqueoData.observaciones = document.getElementById('observaciones').value;

      fetch("{% url 'tpv_shop:guardar_arqueo_auto' %}", {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
          },
          body: JSON.stringify(arqueoData)
      })
      .then(response => response.json())
      .then(data => {
          if (data.status === 'ok') {
              window.location.href = data.redirect_url || "{% url 'tpv_shop:caja_arqueo_list' %}";
          } else {
              throw new Error(data.message || 'Error al guardar el arqueo');
          }
      })
      .catch(error => {
          console.error('Error:', error);
          alert(error.message);
      })
      .finally(() => {
          guardarBtn.disabled = false;
          guardarBtn.innerHTML = '<i class="fas fa-save me-2"></i> Guardar Arqueo';
      });
  });
});