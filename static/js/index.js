const TPV = (function() {
  // Base de datos de productos (simulada)
  let products = [];
  let currentTicket = [];
  let selectedPaymentMethod = null;
  let salesHistory = [];
  let currentUser = null;
  
  // Métodos públicos
  return {
    init: function() {
      this.loadProducts();
      this.loadCurrentUser();
      this.loadSalesHistory();
      this.renderProducts();
      this.updateTicket();
      this.setupEventListeners();
    },
    
    loadProducts: function() {
      // Simulación de carga de productos desde API/localStorage
      const savedProducts = localStorage.getItem('tpv_products');
      products = savedProducts ? JSON.parse(savedProducts) : [
        { id: 1, name: "Café Americano", price: 2.50, category: "Bebidas", stock: 50, barcode: "123456789" },
        { id: 2, name: "Café Espresso", price: 1.80, category: "Bebidas", stock: 30, barcode: "987654321" },
        { id: 3, name: "Té Verde", price: 2.00, category: "Bebidas", stock: 40, barcode: "456123789" }
      ];
    },
    
    loadCurrentUser: function() {
      // Simulación de usuario logueado
      currentUser = {
        id: 1,
        username: "admin",
        name: "Administrador",
        role: "admin"
      };
    },
    
    loadSalesHistory: function() {
      // Simulación de carga de historial desde API/localStorage
      const savedHistory = localStorage.getItem('tpv_sales_history');
      salesHistory = savedHistory ? JSON.parse(savedHistory) : [];
    },
    
    saveProducts: function() {
      localStorage.setItem('tpv_products', JSON.stringify(products));
    },
    
    saveSalesHistory: function() {
      localStorage.setItem('tpv_sales_history', JSON.stringify(salesHistory));
    },
    
    renderProducts: function(filter = '') {
      const container = document.getElementById('products-container');
      container.innerHTML = '';
      
      const filteredProducts = products.filter(product => 
        product.name.toLowerCase().includes(filter.toLowerCase()) || 
        product.category.toLowerCase().includes(filter.toLowerCase()) ||
        (product.barcode && product.barcode.includes(filter))
      );
      
      if (filteredProducts.length === 0) {
        container.innerHTML = `
          <div class="col-12 text-center py-5">
            <i class="fas fa-box-open fa-3x mb-3 text-muted"></i>
            <p class="text-muted">No se encontraron productos</p>
          </div>
        `;
        return;
      }
      
      filteredProducts.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'col-md-4 col-sm-6';
        productCard.innerHTML = `
          <div class="product-card card p-3 mb-3" onclick="TPV.addToTicket(${product.id})" data-id="${product.id}">
            <h6 class="mb-1">${product.name}</h6>
            <p class="text-muted small mb-2">${product.category}</p>
            <div class="d-flex justify-content-between align-items-center">
              <span class="fw-bold">${product.price.toFixed(2)} €</span>
              <span class="badge ${product.stock > 10 ? 'bg-secondary' : 'bg-danger'}">Stock: ${product.stock}</span>
            </div>
          </div>
        `;
        container.appendChild(productCard);
      });
    },
    
    searchProducts: function() {
      const searchTerm = document.getElementById('product-search').value;
      this.renderProducts(searchTerm);
    },
    
    addToTicket: function(productId) {
      const product = products.find(p => p.id === productId);
      if (!product) return;
      
      // Verificar stock
      if (product.stock <= 0) {
        this.showAlert('No hay suficiente stock', 'danger');
        return;
      }
      
      const existingItem = currentTicket.find(item => item.id === productId);
      
      if (existingItem) {
        // Verificar si supera el stock al incrementar
        if (existingItem.quantity + 1 > product.stock) {
          this.showAlert('No hay suficiente stock', 'danger');
          return;
        }
        existingItem.quantity++;
      } else {
        currentTicket.push({
          id: productId,
          name: product.name,
          price: product.price,
          quantity: 1,
          stock: product.stock
        });
      }
      
      this.updateTicket();
    },
    
    updateTicket: function() {
      const ticketList = document.getElementById('ticket-list');
      const itemsCount = document.getElementById('items-count');
      const subtotalElement = document.getElementById('subtotal');
      const ivaElement = document.getElementById('iva');
      const totalElement = document.getElementById('total');
      const totalToPay = document.getElementById('total-to-pay');
      
      ticketList.innerHTML = '';
      
      let subtotal = 0;
      
      currentTicket.forEach(item => {
        const itemTotal = item.price * item.quantity;
        subtotal += itemTotal;
        
        const row = document.createElement('tr');
        row.className = 'ticket-item';
        row.innerHTML = `
          <td>
            ${item.name}
            <span class="delete-item float-end" onclick="TPV.removeFromTicket(${item.id}, event)">
              <i class="fas fa-times"></i>
            </span>
          </td>
          <td class="text-center">
            <div class="d-flex justify-content-center align-items-center">
              <button class="quantity-btn" onclick="TPV.changeQuantity(${item.id}, -1, event)">-</button>
              <input type="text" class="quantity-input" value="${item.quantity}" 
                     onchange="TPV.updateQuantity(${item.id}, this.value)" 
                     onkeyup="this.onchange()" 
                     onpaste="this.onchange()" 
                     oninput="this.onchange()">
              <button class="quantity-btn" onclick="TPV.changeQuantity(${item.id}, 1, event)">+</button>
            </div>
          </td>
          <td class="text-end">${item.price.toFixed(2)} €</td>
          <td class="text-end">${itemTotal.toFixed(2)} €</td>
        `;
        ticketList.appendChild(row);
      });
      
      const iva = subtotal * 0.21;
      const total = subtotal + iva;
      
      itemsCount.textContent = currentTicket.reduce((sum, item) => sum + item.quantity, 0);
      subtotalElement.textContent = subtotal.toFixed(2) + ' €';
      ivaElement.textContent = iva.toFixed(2) + ' €';
      totalElement.textContent = total.toFixed(2) + ' €';
      totalToPay.textContent = total.toFixed(2) + ' €';
      
      // Actualizar el campo de importe con el total
      document.getElementById('importe').value = total.toFixed(2);
    },
    
    changeQuantity: function(productId, delta, event) {
      event.stopPropagation();
      const item = currentTicket.find(item => item.id === productId);
      if (item) {
        const newQuantity = item.quantity + delta;
        
        // Verificar stock
        if (newQuantity > item.stock) {
          this.showAlert('No hay suficiente stock', 'danger');
          return;
        }
        
        if (newQuantity < 1) {
          this.removeFromTicket(productId, event);
          return;
        }
        
        item.quantity = newQuantity;
        this.updateTicket();
      }
    },
    
    updateQuantity: function(productId, newQuantity) {
      const quantity = parseInt(newQuantity);
      if (isNaN(quantity)) return;
      
      const item = currentTicket.find(item => item.id === productId);
      if (item) {
        // Verificar stock
        if (quantity > item.stock) {
          this.showAlert('No hay suficiente stock', 'danger');
          this.updateTicket(); // Para resetear el valor
          return;
        }
        
        if (quantity < 1) {
          this.removeFromTicket(productId);
          return;
        }
        
        item.quantity = quantity;
        this.updateTicket();
      }
    },
    
    removeFromTicket: function(productId, event) {
      if (event) event.stopPropagation();
      currentTicket = currentTicket.filter(item => item.id !== productId);
      this.updateTicket();
    },
    
    clearTicket: function() {
      if (currentTicket.length === 0) return;
      
      if (confirm('¿Estás seguro de que quieres cancelar este ticket?')) {
        currentTicket = [];
        this.updateTicket();
        document.getElementById('importe').value = '';
        selectedPaymentMethod = null;
        this.resetPaymentMethods();
      }
    },
    
    // Funciones para la calculadora
    addNumber: function(num) {
      const input = document.getElementById('importe');
      if (num === '.' && input.value.includes('.')) return;
      if (input.value === '0' && num !== '.') input.value = '';
      input.value += num;
    },
    
    clearInput: function() {
      document.getElementById('importe').value = '';
    },
    
    // Funciones para los métodos de pago
    selectPayment: function(method) {
      selectedPaymentMethod = method;
      this.resetPaymentMethods();
      document.getElementById(`${method}-payment`).classList.add('active');
    },
    
    resetPaymentMethods: function() {
      document.querySelectorAll('.payment-method').forEach(el => {
        el.classList.remove('active');
      });
    },
    
    // Función para procesar el pago
    processPayment: function() {
      if (currentTicket.length === 0) {
        this.showAlert('No hay productos en el ticket', 'warning');
        return;
      }
      
      if (!selectedPaymentMethod) {
        this.showAlert('Selecciona un método de pago', 'warning');
        return;
      }
      
      const total = parseFloat(document.getElementById('total').textContent.replace(' €', '').replace(',', ''));
      document.getElementById('modal-total').textContent = total.toFixed(2) + ' €';
      
      // Mostrar el modal de pago
      const paymentModal = new bootstrap.Modal(document.getElementById('paymentModal'));
      paymentModal.show();
      
      // Configurar campos según método de pago
      const paymentAmountField = document.getElementById('payment-amount');
      const paymentAmountLabel = document.querySelector('label[for="payment-amount"]');
      const changeContainer = document.getElementById('change-container');
      
      if (selectedPaymentMethod === 'efectivo') {
        paymentAmountField.style.display = 'block';
        paymentAmountLabel.style.display = 'block';
        paymentAmountField.value = '';
        paymentAmountField.focus();
        changeContainer.style.display = 'none';
      } else {
        paymentAmountField.style.display = 'none';
        paymentAmountLabel.style.display = 'none';
        changeContainer.style.display = 'none';
      }
    },
    
    calculateChange: function() {
      const total = parseFloat(document.getElementById('total').textContent.replace(' €', '').replace(',', ''));
      const amount = parseFloat(document.getElementById('payment-amount').value.replace(',', '.')) || 0;
      
      if (amount >= total) {
        const change = amount - total;
        document.getElementById('change-amount').textContent = change.toFixed(2) + ' €';
        document.getElementById('change-container').style.display = 'block';
      } else {
        document.getElementById('change-container').style.display = 'none';
      }
    },
    
    confirmPayment: function() {
      const total = parseFloat(document.getElementById('total').textContent.replace(' €', '').replace(',', ''));
      const paymentAmount = document.getElementById('payment-amount').value;
      
      // Validar pago en efectivo
      if (selectedPaymentMethod === 'efectivo' && (!paymentAmount || isNaN(parseFloat(paymentAmount.replace(',', '.'))) || parseFloat(paymentAmount.replace(',', '.')) < total)) {
        this.showAlert('La cantidad recibida no puede ser menor que el total', 'danger');
        return;
      }
      
      // Crear un nuevo registro en el historial
      const newSale = {
        id: salesHistory.length > 0 ? Math.max(...salesHistory.map(s => s.id)) + 1 : 1,
        date: new Date().toLocaleString('es-ES'),
        total: total,
        method: selectedPaymentMethod,
        user: currentUser.username,
        items: currentTicket.map(item => ({
          productId: item.id,
          product: item.name,
          quantity: item.quantity,
          price: item.price
        }))
      };
      
      // Actualizar stock de productos
      currentTicket.forEach(item => {
        const product = products.find(p => p.id === item.id);
        if (product) {
          product.stock -= item.quantity;
        }
      });
      
      // Guardar en el historial
      salesHistory.unshift(newSale);
      this.saveSalesHistory();
      this.saveProducts();
      
      // Mostrar mensaje de éxito
      this.showAlert(`Pago de ${total.toFixed(2)} € realizado con éxito (${this.getPaymentMethodName(selectedPaymentMethod)})`, 'success');
      
      // Imprimir ticket (simulado)
      this.printTicket(newSale);
      
      // Cerrar el modal y limpiar el ticket
      const paymentModal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
      paymentModal.hide();
      
      currentTicket = [];
      this.updateTicket();
      document.getElementById('importe').value = '';
      selectedPaymentMethod = null;
      this.resetPaymentMethods();
      
      // Actualizar la lista de productos (por si cambió el stock)
      this.renderProducts();
      this.updateSalesSummary();
    },
    
    printTicket: function(sale) {
      // En una implementación real, aquí se enviaría a una impresora térmica
      console.log('=== TICKET DE VENTA ===');
      console.log(`Fecha: ${sale.date}`);
      console.log('-----------------------');
      sale.items.forEach(item => {
        console.log(`${item.quantity} x ${item.product} - ${item.price.toFixed(2)} €`);
      });
      console.log('-----------------------');
      console.log(`TOTAL: ${sale.total.toFixed(2)} €`);
      console.log(`Método: ${this.getPaymentMethodName(sale.method)}`);
      console.log(`Atendido por: ${sale.user}`);
      console.log('=======================');
    },
    
    getPaymentMethodName: function(method) {
      switch(method) {
        case 'efectivo': return 'Efectivo';
        case 'tarjeta': return 'Tarjeta';
        case 'transferencia': return 'Transferencia';
        default: return 'Otros';
      }
    },
    
    showAlert: function(message, type) {
      const alertDiv = document.createElement('div');
      alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
      alertDiv.style.top = '20px';
      alertDiv.style.right = '20px';
      alertDiv.style.zIndex = '1100';
      alertDiv.style.minWidth = '300px';
      alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      `;
      
      document.body.appendChild(alertDiv);
      
      setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
      }, 3000);
    },
    
    // Funciones para el menú superior
    showSalesSummary: function() {
      const today = new Date().toLocaleDateString('es-ES');
      const todaySales = salesHistory.filter(sale => 
        new Date(sale.date).toLocaleDateString('es-ES') === today
      );
      
      const totalSales = todaySales.reduce((sum, sale) => sum + sale.total, 0);
      const paymentMethods = {};
      
      todaySales.forEach(sale => {
        if (!paymentMethods[sale.method]) {
          paymentMethods[sale.method] = 0;
        }
        paymentMethods[sale.method] += sale.total;
      });
      
      let paymentMethodsHTML = '';
      for (const [method, total] of Object.entries(paymentMethods)) {
        paymentMethodsHTML += `
          <tr>
            <td>${this.getPaymentMethodName(method)}</td>
            <td class="text-end">${total.toFixed(2)} €</td>
          </tr>
        `;
      }
      
      document.getElementById('sales-today').textContent = today;
      document.getElementById('sales-total-amount').textContent = totalSales.toFixed(2) + ' €';
      document.getElementById('sales-total-count').textContent = todaySales.length;
      document.getElementById('sales-by-method').innerHTML = paymentMethodsHTML;
      
      const salesModal = new bootstrap.Modal(document.getElementById('salesModal'));
      salesModal.show();
    },
    
    showInventory: function() {
      let inventoryHTML = '';
      let totalValue = 0;
      
      products.forEach(product => {
        const productValue = product.price * product.stock;
        totalValue += productValue;
        
        inventoryHTML += `
          <tr>
            <td>${product.name}</td>
            <td class="text-center">${product.stock}</td>
            <td class="text-end">${product.price.toFixed(2)} €</td>
            <td class="text-end">${productValue.toFixed(2)} €</td>
          </tr>
        `;
      });
      
      document.getElementById('inventory-total-value').textContent = totalValue.toFixed(2) + ' €';
      document.getElementById('inventory-total-items').textContent = products.length;
      document.getElementById('inventory-items-list').innerHTML = inventoryHTML;
      
      const inventoryModal = new bootstrap.Modal(document.getElementById('inventoryModal'));
      inventoryModal.show();
    },
    
    addNewProduct: function() {
      const form = document.getElementById('new-product-form');
      const formData = new FormData(form);
      
      const newProduct = {
        id: products.length > 0 ? Math.max(...products.map(p => p.id)) + 1 : 1,
        name: formData.get('name'),
        price: parseFloat(formData.get('price').replace(',', '.')),
        category: formData.get('category'),
        stock: parseInt(formData.get('stock')),
        barcode: formData.get('barcode')
      };
      
      // Validaciones básicas
      if (!newProduct.name || isNaN(newProduct.price) || isNaN(newProduct.stock)) {
        this.showAlert('Por favor complete todos los campos correctamente', 'danger');
        return;
      }
      
      products.push(newProduct);
      this.saveProducts();
      this.renderProducts();
      
      this.showAlert('Producto añadido correctamente', 'success');
      
      const productModal = bootstrap.Modal.getInstance(document.getElementById('productModal'));
      productModal.hide();
      
      form.reset();
    },
    
    updateSalesSummary: function() {
      const today = new Date().toLocaleDateString('es-ES');
      const todaySales = salesHistory.filter(sale => 
        new Date(sale.date).toLocaleDateString('es-ES') === today
      );
      
      const totalSales = todaySales.reduce((sum, sale) => sum + sale.total, 0);
      document.getElementById('daily-sales-amount').textContent = totalSales.toFixed(2) + ' €';
      document.getElementById('daily-sales-count').textContent = todaySales.length;
    },
    
    setupEventListeners: function() {
      // Event listener para el teclado físico
      document.addEventListener('keydown', (e) => {
        if (e.key >= '0' && e.key <= '9') {
          this.addNumber(e.key);
        } else if (e.key === '.' || e.key === ',') {
          this.addNumber('.');
        } else if (e.key === 'Enter') {
          this.processPayment();
        } else if (e.key === 'Escape') {
          this.clearInput();
        } else if (e.key === 'Delete') {
          this.clearTicket();
        }
      });
    }
  };
})();