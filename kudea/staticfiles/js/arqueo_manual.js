document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let isShift = false;
    let activeInput = null;
    let currentOperation = null;
    let firstOperand = null;
    
    // Seleccionar todos los inputs numéricos
    const numericInputs = document.querySelectorAll('input[type="text"]:not(#id_observaciones)');
    
    // Seleccionar el input de observaciones por separado
    const observacionesInput = document.getElementById('id_observaciones');
    
    // Función para manejar el foco en los inputs
    numericInputs.forEach(input => {
      input.addEventListener('focus', function() {
        activeInput = this;
        document.getElementById('btnNumbers').click();
      });
    });
    
    observacionesInput.addEventListener('focus', function() {
      activeInput = this;
      document.getElementById('btnLetters').click();
    });
    
    // Función para añadir caracteres
    function addChar(char) {
      if (!activeInput) return;
      
      // Validaciones para campos numéricos
      if (activeInput !== observacionesInput) {
        // Si es el primer caracter y es un punto, agregar 0 primero
        if (activeInput.value === '' && char === '.') {
          activeInput.value = '0.';
          return;
        }
        
        // Si ya hay un punto, no permitir otro
        if (char === '.' && activeInput.value.includes('.')) {
          return;
        }
        
        // Limitar a 2 decimales después del punto
        if (activeInput.value.includes('.')) {
          const decimalPart = activeInput.value.split('.')[1];
          if (decimalPart && decimalPart.length >= 2) {
            return;
          }
        }
      }
      
      activeInput.value += isShift ? char.toUpperCase() : char;
      calcularDiferencia();
    }
    
    // Función para borrar
    function deleteChar() {
      if (!activeInput) return;
      activeInput.value = activeInput.value.slice(0, -1);
      calcularDiferencia();
    }
    
    // Función para calcular diferencia
    function calcularDiferencia() {
      const efectivoInicial = parseFloat(document.getElementById("id_efectivo_inicial").value) || 0;
      const efectivoFinal = parseFloat(document.getElementById("id_efectivo_final").value) || 0;
      const diferencia = efectivoFinal - efectivoInicial;
      
      document.getElementById("diferencia").textContent = diferencia.toFixed(2) + ' €';
      
      // Cambiar color según el resultado
      const diferenciaElement = document.getElementById("diferencia");
      if (diferencia > 0) {
        diferenciaElement.style.color = '#00b894'; // Verde
      } else if (diferencia < 0) {
        diferenciaElement.style.color = '#d63031'; // Rojo
      } else {
        diferenciaElement.style.color = '#2d3436'; // Negro
      }
    }
    
    // Mapeo de teclas
    document.querySelectorAll('.keyboard-key[data-char]').forEach(key => {
      key.addEventListener('click', () => addChar(key.getAttribute('data-char')));
    });
    
    // Tecla de borrado
    document.querySelectorAll('.keyboard-key-delete').forEach(btn => {
      btn.addEventListener('click', deleteChar);
    });
    
    // Shift (mayúsculas/minúsculas)
    document.querySelector('.keyboard-key-shift')?.addEventListener('click', () => {
      isShift = !isShift;
      document.querySelectorAll('#lettersKeyboard .keyboard-key[data-char]').forEach(key => {
        const char = key.getAttribute('data-char');
        if (/[a-zñáéíóú]/.test(char)) {
          key.textContent = isShift ? char.toUpperCase() : char.toLowerCase();
        }
      });
    });
    
    // Alternar entre teclados
    document.getElementById('btnLetters').addEventListener('click', function() {
      this.classList.add('active');
      document.getElementById('btnNumbers').classList.remove('active');
      document.getElementById('lettersKeyboard').style.display = 'block';
      document.getElementById('numbersKeyboard').style.display = 'none';
    });
    
    document.getElementById('btnNumbers').addEventListener('click', function() {
      this.classList.add('active');
      document.getElementById('btnLetters').classList.remove('active');
      document.getElementById('lettersKeyboard').style.display = 'none';
      document.getElementById('numbersKeyboard').style.display = 'block';
    });
    
    // Operaciones matemáticas para el teclado numérico
    document.querySelectorAll('[data-action="add"], [data-action="subtract"], [data-action="multiply"], [data-action="divide"]').forEach(btn => {
      btn.addEventListener('click', function() {
        if (activeInput && activeInput.value) {
          firstOperand = parseFloat(activeInput.value);
          currentOperation = this.getAttribute('data-action');
          activeInput.value = '';
        }
      });
    });
    
    // Calcular diferencia cuando cambia el efectivo inicial
    document.getElementById("id_efectivo_inicial").addEventListener('input', calcularDiferencia);
  });